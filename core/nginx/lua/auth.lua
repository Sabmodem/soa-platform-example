local cjson = require "cjson"

local auth_header = ngx.var.http_authorization
local token = nil

if auth_header then
    token = string.match(auth_header, "Bearer%s+(.+)")
end

local opa_input = {
    input = {
        token = token,
        method = ngx.var.request_method,
        path = ngx.var.request_uri,
        headers = ngx.req.get_headers(),
        source_ip = ngx.var.remote_addr,
        timestamp = ngx.time()
    }
}

local res = ngx.location.capture("/opa/check", {
    method = ngx.HTTP_POST,
    body = cjson.encode(opa_input),
    always_forward_body = true
})

if res.status ~= 200 then
    ngx.log(ngx.ERR, "OPA request failed with status: ", res.status)
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
    return
end

local response = cjson.decode(res.body)

if response.result == true then
    if response.headers then
        for k, v in pairs(response.headers) do
            ngx.header["X-Auth-" .. k] = v
        end
    end
    
    ngx.exit(ngx.HTTP_OK)
else
    ngx.status = ngx.HTTP_FORBIDDEN
    ngx.say(cjson.encode({
        error = "Access denied",
        reason = response.reason or "Policy violation"
    }))
    ngx.exit(ngx.HTTP_FORBIDDEN)
end