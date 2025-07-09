# Service oriented platform example
The platform was built based nginx as api gateway and opa for centralized authorization. The platform has a main frontend that combines all services frontends using module federation technology. The current version of platform was designed as test version, it never have tested on any production environments.

## Quickstart
```
Bash
docker compose -f ./docker-compose.core.yml up -d
docker compose -f ./docker-compose.services.yml up -d
```

## Usage
- Go to the browser and open url ```http://localhost:80```. You will see the main platform interface.
- Authorize with credentials ```abc:abc``` to access the test service. You will see the menu in left side of interface. The menu will have a list of all allowed services. In that case you will have only one service
- Authorize with credentials ```bca:bca```. The account dont have access to the test service. After authorization you will see an empty list at the left side menu

## Notice
The platform does not have a client side route protection, so you may open the test service interface in all cases, but the test service api was strongly protected by opa. You may use the service only under ```abc:abc``` account. The platform has support of client side route protection, but this feature was removed from the test version to keep simplicity
