# Dashboard Variable Schema Contract

## Purpose

Return the variable input schema for one administrator-selected prompt version. This dashboard-only interface is separate from the API-key SDK fetch API.

## Endpoint

`GET /dashboard/api/versions/{version_id}/variables/`

## Authorization

- Requires an authenticated Django session user with staff or superuser permission.
- Unauthenticated users follow the existing dashboard login redirect behavior.
- Non-staff users follow the existing dashboard permission-denial behavior.
- API-key authentication does not authorize this endpoint.

## Successful response

Status: `200 OK`

```json
{
  "prompt": {"id": 42, "slug": "support-reply", "name": "Support Reply"},
  "version": {"id": 101, "number": 3, "status": "draft"},
  "variables": [
    {
      "name": "customer_name",
      "var_type": "string",
      "required": true,
      "default_value": null,
      "description": "Name shown in the greeting"
    }
  ]
}
```

- Variables are ordered by name.
- The response includes no template content or sections.
- `default_value: null` means there is no default and must not become an empty string.
- Authorized staff users can query draft and published versions.

## Error and method behavior

| Situation | Expected behavior |
|---|---|
| Unknown version | `404 Not Found`, with no schema disclosure |
| Unsupported HTTP method | `405 Method Not Allowed` |
| Unauthenticated request | Existing dashboard login redirect |
| Authenticated non-staff request | Existing dashboard access denial |

## Related page

`GET /dashboard/versions/{version_id}/playground/` is a staff-only screen reached from the selected version detail toolbar. It has no standalone prompt/version selector.
