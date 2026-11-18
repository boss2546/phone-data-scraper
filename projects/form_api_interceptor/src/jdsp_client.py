"""
JDSP GraphQL API Client
Target: https://aiisapp.cloud (Joint Digital Service Platform)
Auth: Keycloak OIDC (https://auth.aiisapp.cloud/realms/jdsp-prod)
"""

import requests
from typing import Dict, Any, List, Optional


class JDSPClient:
    AUTH_URL = "https://auth.aiisapp.cloud/realms/jdsp-prod/protocol/openid-connect/token"
    API_URL = "https://api.aiisapp.cloud/query"
    CLIENT_ID = "web-client"

    def __init__(self, refresh_token: str):
        self.refresh_token_str = refresh_token
        self.access_token: Optional[str] = None
        self.session = requests.Session()
        self.authenticate()

    def authenticate(self) -> None:
        """รีเฟรช Access Token จาก Keycloak อัตโนมัติ"""
        res = self.session.post(self.AUTH_URL, data={
            "grant_type": "refresh_token",
            "client_id": self.CLIENT_ID,
            "refresh_token": self.refresh_token_str
        }, timeout=10)
        res.raise_for_status()
        data = res.json()
        self.access_token = data["access_token"]
        if "refresh_token" in data:
            self.refresh_token_str = data["refresh_token"]

        self.session.headers.update({
            "accept": "application/graphql-response+json,application/json;q=0.9",
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json"
        })

    def execute_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None, operation_name: Optional[str] = None) -> Dict[str, Any]:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        res = self.session.post(self.API_URL, json=payload, timeout=15)
        if res.status_code == 401:
            # Re-authenticate on token expiry
            self.authenticate()
            res = self.session.post(self.API_URL, json=payload, timeout=15)

        res.raise_for_status()
        result = res.json()
        if "errors" in result:
            raise RuntimeError(f"GraphQL Errors: {result['errors']}")
        return result.get("data", {})

    def list_users(self, keyword: str = "", page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        query = """
        query listUsers($page: Int!, $pageSize: Int!, $keyword: String, $jFunctionCode: String, $roleId: ID, $status: String) {
          listUsers(
            page: $page
            pageSize: $pageSize
            keyword: $keyword
            jFunctionCode: $jFunctionCode
            roleId: $roleId
            status: $status
          ) {
            items {
              id
              accountName
              firstName
              lastName
              email
              status
              jFunctionCode
              avatarImg
              description
              roleNames
            }
            pageInfo {
              page
              pageSize
              total
              totalPages
            }
          }
        }
        """
        variables = {"page": page, "pageSize": page_size}
        if keyword:
            variables["keyword"] = keyword
        return self.execute_graphql(query, variables, "listUsers").get("listUsers", {})

    def save_user(
        self,
        account_name: str,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role_ids: List[str],
        j_function_code: str = "J3",
        description: str = "",
        avatar_img: Optional[str] = None
    ) -> Dict[str, Any]:
        query = """
        mutation SaveUser($id: String, $accountName: String!, $firstName: String!, $lastName: String!, $email: String!, $password: String!, $roleIds: [String!]!, $description: String, $avatarImg: String, $jFunctionCode: String!) {
          saveUser(
            id: $id
            accountName: $accountName
            firstName: $firstName
            lastName: $lastName
            email: $email
            password: $password
            roleIds: $roleIds
            description: $description
            avatarImg: $avatarImg
            jFunctionCode: $jFunctionCode
          ) {
            accountName
            __typename
          }
        }
        """
        variables = {
            "id": None,
            "accountName": account_name,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "password": password,
            "roleIds": role_ids,
            "jFunctionCode": j_function_code,
            "description": description,
            "avatarImg": avatar_img
        }
        return self.execute_graphql(query, variables, "SaveUser").get("saveUser", {})

    def delete_user(self, user_id: str) -> bool:
        query = """
        mutation DeleteUser($id: String!) {
          deleteUser(id: $id)
        }
        """
        return self.execute_graphql(query, {"id": user_id}, "DeleteUser").get("deleteUser", False)
