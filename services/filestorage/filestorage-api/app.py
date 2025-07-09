import os
import uuid
import logging
import typing
import jwt
import httpx
from datetime import datetime

from fastapi import FastAPI, Depends, UploadFile, HTTPException, status
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import FileResponse
from pydantic import BaseModel

import aiofiles

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

FILES_DIR = os.getenv('FILES_DIR', 'uploaded_files')
STATIC_FILES_DIR = os.getenv('STATIC_FILES_DIR', 'static')
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'myrealm')

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(STATIC_FILES_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileInfo(BaseModel):
    filename: str
    path: str
    uploaded_at: datetime

cached_pem_public_key: typing.Optional[str] = None

def _decode_base64url_to_int(value: str) -> int:
    decoded = base64.urlsafe_b64decode(value + '==')
    return int.from_bytes(decoded, byteorder='big')

async def get_keycloak_public_key_pem() -> typing.Optional[str]:
    """
    Fetches the JWKS from Keycloak, extracts the RS256 signature public key,
    and converts it to PEM format.
    """
    global cached_pem_public_key
    if cached_pem_public_key:
        return cached_pem_public_key

    try:
        certs_url = f"{KEYCLOAK_URL}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
        async with httpx.AsyncClient() as client:
            response = await client.get(certs_url, timeout=5)
            response.raise_for_status()
            jwks = response.json()

            target_key = None
            for key in jwks.get('keys', []):
                if key.get('use') == 'sig' and key.get('alg') == 'RS256' and key.get('kty') == 'RSA':
                    target_key = key
                    break
            
            if not target_key:
                logger.error(f"No suitable RS256 signature key found in Keycloak JWKS: {jwks}")
                return None

            n = _decode_base64url_to_int(target_key['n'])
            e = _decode_base64url_to_int(target_key['e'])

            public_numbers = rsa.RSAPublicNumbers(e=e, n=n)
            
            public_key = public_numbers.public_key(default_backend())

            pem_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            cached_pem_public_key = pem_key
            logger.info("Successfully fetched and converted Keycloak public key to PEM format.")
            return cached_pem_public_key

    except httpx.RequestError as e:
        logger.error(f"Network error while fetching Keycloak public key: {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON decoding error or unexpected Keycloak response: {e}")
        return None
    except KeyError as e:
        logger.error(f"Missing key component in JWK: {e}. Full JWK: {target_key}")
        return None
    except Exception as e:
        logger.critical(f"An unhandled error occurred during public key retrieval/conversion: {e}", exc_info=True)
        return None

app = FastAPI(
    title="File Storage Service",
    description="A simple microservice for storing and retrieving files.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")

async def get_current_user(request: Request) -> typing.Optional[dict]:
    """
    Authenticates user based on Authorization header and decodes JWT.
    Raises HTTPException for invalid tokens.
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization scheme must be Bearer",
                headers={"WWW-Authenticate": "Bearer"},
            )

        pem_public_key = await get_keycloak_public_key_pem()
        if not pem_public_key:
            logger.error("Keycloak PEM public key not available, cannot authenticate.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable.",
            )
        
        decoded_token = jwt.decode(
            token,
            pem_public_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_signature": True
            }
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authorization header format: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during user authentication: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during authentication.",
        )

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the File Storage Service. Visit /docs for API documentation."}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Endpoint for health checks."""
    return {"status": "healthy"}

@app.get('/files', response_model=list[FileInfo])
async def list_files(user: dict = Depends(get_current_user)):
    """
    Lists all available files.
    Requires authentication.
    """
    files_list = []
    for filename in os.listdir(FILES_DIR):
        filepath = os.path.join(FILES_DIR, filename)
        if os.path.isfile(filepath):
            files_list.append(FileInfo(
                filename=filename,
                path=f"/files/{filename}",
                uploaded_at=datetime.fromtimestamp(os.path.getmtime(filepath))
            ))
    return files_list

@app.post('/files', status_code=status.HTTP_201_CREATED)
async def upload_files(files: list[UploadFile], user: dict = Depends(get_current_user)):
    """
    Uploads one or more files to the service.
    Requires authentication.
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided for upload.")

    uploaded_filenames = []
    for file in files:
        if file.filename is None:
            logger.warning("Received an uploaded file without a filename.")
            continue

        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(FILES_DIR, unique_filename)

        MAX_FILE_SIZE_MB = 50
        MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

        try:
            async with aiofiles.open(file_path, 'wb') as outfile:
                file_size = 0
                while True:
                    chunk = await file.read(8192)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE_BYTES:
                        await outfile.close()
                        os.remove(file_path)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File '{file.filename}' exceeds the maximum allowed size of {MAX_FILE_SIZE_MB}MB."
                        )
                    await outfile.write(chunk)
            uploaded_filenames.append(unique_filename)
            logger.info(f"File '{file.filename}' uploaded successfully as '{unique_filename}' by user: {user.get('preferred_username', 'N/A')}")
        except Exception as e:
            logger.error(f"Failed to upload file '{file.filename}': {e}", exc_info=True)
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not upload file '{file.filename}'"
            )
    return {"message": "Files uploaded successfully", "uploaded_files": uploaded_filenames}

@app.get('/files/{filename}')
async def get_file(filename: str, user: dict = Depends(get_current_user)):
    """
    Retrieves a specific file by its filename.
    Requires authentication.
    """
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(FILES_DIR, safe_filename)

    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        logger.info(f"Attempted to access non-existent file: {safe_filename} by user: {user.get('preferred_username', 'N/A')}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{safe_filename}' not found."
        )
    
    logger.info(f"Serving file: {safe_filename} to user: {user.get('preferred_username', 'N/A')}")
    return FileResponse(filepath, filename=safe_filename)

@app.delete('/files/{filename}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(filename: str, user: dict = Depends(get_current_user)):
    """
    Deletes a specific file by its filename.
    Requires authentication.
    """
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(FILES_DIR, safe_filename)

    try:
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{safe_filename}' not found."
            )
        
        os.remove(filepath)
        logger.info(f"File '{safe_filename}' deleted successfully by user: {user.get('preferred_username', 'N/A')}")
        return {"message": f"File '{safe_filename}' deleted successfully."}
    except OSError as e:
        logger.error(f"Error deleting file '{safe_filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete file '{safe_filename}' due to an internal error."
        )

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Attempting to fetch Keycloak public key in PEM format...")
    await get_keycloak_public_key_pem()
    if not cached_pem_public_key:
        logger.warning("Keycloak public key (PEM) could not be fetched at startup. Authentication may fail.")