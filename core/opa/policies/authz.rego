package authz
default allow = false

public_paths = {
    "/",
    "/health",
    "/login",
    "/api/public"
}

allow if {
    input.path = public_paths[_]
}

allow if {
    startswith(input.path, "/auth/")
}

allow if {
    regex.match("^.*\\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$", input.path)
}

jwt_payload := payload if {
    input.token
    token := replace(input.token, "Bearer ", "")
    parts := split(token, ".")
    count(parts) == 3
    payload := json.unmarshal(base64url.decode(parts[1]))
} else := {}

token_valid if {
    jwt_payload.exp
    now := time.now_ns() / 1000000000
    jwt_payload.exp > now
}

user_roles := roles if {
    jwt_payload.realm_access.roles
    roles := jwt_payload.realm_access.roles
} else := []

allow if {
    startswith(input.path, "/api/admin/")
    token_valid
    "admin" = user_roles[_]
}

allow if {
    startswith(input.path, "/api/filestorage/")
    token_valid
    filestorage_roles = {"module-filestorage", "admin"}
    user_roles[_] = filestorage_roles[_]
}

debug := {
    "token_valid": token_valid,
    "user_roles": user_roles,
    "username": jwt_payload.preferred_username,
    "path": input.path
}

message := "Access denied: no token" if {
    not input.token
    not is_public_path
    not startswith(input.path, "/auth/")
}

is_public_path if {
    input.path = public_paths[_]
}

message := "Access denied: token expired" if {
    input.token
    not token_valid
}

message := "Access denied: insufficient permissions" if {
    token_valid
    not allow
}