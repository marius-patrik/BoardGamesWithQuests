# API reference — intended FastAPI HTTP behavior

This file is a **design reference**, not the deployed API specification or a source for generated clients. The Python FastAPI routes and their typed Pydantic models will generate the **actual** OpenAPI contract when implemented; production clients derive types from that generated output, not by extracting a document from this folder.

The following OpenAPI 3.1 example records the intended endpoints, responses, authentication, CSRF, revision, idempotency and participant boundaries before implementation. Review/contract checks may parse it to detect contradictions with the database/engine model, but passing that check **does not** establish that corresponding routes or types exist. The example requires that a new browser can get anonymous CSRF via `GET /session`, then submit guest/login/register operations using that token; final behavior must be exercised against the running service.

```yaml
openapi: 3.1.0
info:
  title: BoardGamesWithQuests API
  version: 1.0.0
  description: Authoritative board game, configuration, identity, and asset API.
servers:
- url: /api/v1
security:
- cookieSession: []
paths:
  /session:
    get:
      tags:
      - Identity
      operationId: getSession
      summary: Read authenticated session or bootstrap anonymous CSRF cookie
      responses:
        '200':
          description: Read session
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
  /auth/guest:
    post:
      tags:
      - Identity
      operationId: createGuest
      summary: Create anonymous identity
      responses:
        '201':
          description: Create anonymous identity
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/register:
    post:
      tags:
      - Identity
      operationId: register
      summary: Create account
      responses:
        '201':
          description: Create account
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Credentials'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/login:
    post:
      tags:
      - Identity
      operationId: login
      summary: Authenticate
      responses:
        '200':
          description: Authenticate
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Credentials'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/upgrade:
    post:
      tags:
      - Identity
      operationId: upgrade
      summary: Upgrade guest without changing user ID
      responses:
        '200':
          description: Upgrade guest without changing user ID
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Credentials'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /auth/logout:
    post:
      tags:
      - Identity
      operationId: logout
      summary: Invalidate session
      responses:
        '204':
          description: Invalidate session
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /me:
    get:
      tags:
      - Accounts
      operationId: getMe
      summary: Read profile
      responses:
        '200':
          description: Read profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Profile'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    patch:
      tags:
      - Accounts
      operationId: updateMe
      summary: Update profile
      responses:
        '200':
          description: Update profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Profile'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProfilePatch'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /me/games:
    get:
      tags:
      - Accounts
      operationId: listMyGames
      summary: List games
      responses:
        '200':
          description: List games
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GameSummary'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /me/awards:
    get:
      tags:
      - Accounts
      operationId: listAwards
      summary: List awards
      responses:
        '200':
          description: List awards
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Award'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /me/ratings:
    get:
      tags:
      - Accounts
      operationId: listRatings
      summary: List ratings
      responses:
        '200':
          description: List ratings
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Rating'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /definitions:
    get:
      tags:
      - Definitions
      operationId: listDefinitions
      summary: List published definitions
      responses:
        '200':
          description: List published definitions
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    post:
      tags:
      - Definitions
      operationId: createDefinition
      summary: Create definition draft
      responses:
        '201':
          description: Create definition draft
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DefinitionCreate'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /definitions/import:
    post:
      tags:
      - Definitions
      operationId: importDefinition
      summary: Import portable JSON as draft
      responses:
        '201':
          description: Import portable JSON as draft
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ConfigDocument'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}:
    get:
      tags:
      - Definitions
      operationId: getDefinition
      summary: Read definition
      responses:
        '200':
          description: Read definition
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
    delete:
      tags:
      - Definitions
      operationId: deleteDefinition
      summary: Delete unreferenced draft-owned definition
      responses:
        '204':
          description: Delete unreferenced draft-owned definition
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/draft:
    get:
      tags:
      - Definitions
      operationId: getDraft
      summary: Read editable version
      responses:
        '200':
          description: Read editable version
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConfigDocument'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
    put:
      tags:
      - Definitions
      operationId: saveDraft
      summary: Replace editable version transactionally
      responses:
        '200':
          description: Replace editable version transactionally
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConfigDocument'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ConfigDocument'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/publish:
    post:
      tags:
      - Definitions
      operationId: publishDefinition
      summary: Validate and publish immutable version
      responses:
        '200':
          description: Validate and publish immutable version
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/duplicate:
    post:
      tags:
      - Definitions
      operationId: duplicateDefinition
      summary: Create an owned copy
      responses:
        '201':
          description: Create an owned copy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Definition'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/versions/{version}/export:
    get:
      tags:
      - Definitions
      operationId: exportVersion
      summary: Export portable JSON incl. assets
      responses:
        '200':
          description: Export portable JSON incl. assets
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConfigDocument'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/version'
  /definitions/{definitionId}/assets:
    post:
      tags:
      - Assets
      operationId: beginUpload
      summary: Create restricted temporary upload grant
      responses:
        '201':
          description: Create restricted temporary upload grant
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssetUpload'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AssetUploadRequest'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/assets/{assetId}/finalize:
    post:
      tags:
      - Assets
      operationId: finalizeUpload
      summary: Verify integrity and mark ready
      responses:
        '200':
          description: Verify integrity and mark ready
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Asset'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/assetId'
      - $ref: '#/components/parameters/csrf'
  /definitions/{definitionId}/assets/{assetId}:
    delete:
      tags:
      - Assets
      operationId: deleteAsset
      summary: Delete unreferenced draft asset
      responses:
        '204':
          description: Delete unreferenced draft asset
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/assetId'
      - $ref: '#/components/parameters/csrf'
    get:
      tags:
      - Assets
      operationId: getAsset
      summary: Get authorized short-lived access
      responses:
        '200':
          description: Get authorized short-lived access
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AssetUpload'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/definitionId'
      - $ref: '#/components/parameters/assetId'
  /games:
    post:
      tags:
      - Games
      operationId: createGame
      summary: Create invitation
      responses:
        '201':
          description: Create invitation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Game'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GameCreate'
      parameters:
      - $ref: '#/components/parameters/csrf'
  /games/{gameId}:
    get:
      tags:
      - Games
      operationId: getGame
      summary: Read authorized authoritative projection
      responses:
        '200':
          description: Read authorized authoritative projection
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Game'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
  /games/{gameId}/invitation:
    get:
      tags:
      - Games
      operationId: getInvitation
      summary: Preview invitation
      responses:
        '200':
          description: Preview invitation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Invitation'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
  /games/{gameId}/join:
    post:
      tags:
      - Games
      operationId: joinGame
      summary: Join existing game idempotently
      responses:
        '200':
          description: Join existing game idempotently
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Game'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/JoinRequest'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - $ref: '#/components/parameters/csrf'
  /games/{gameId}/available-actions:
    get:
      tags:
      - Games
      operationId: availableActions
      summary: Generate available actor actions
      responses:
        '200':
          description: Generate available actor actions
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AvailableAction'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
  /games/{gameId}/actions:
    post:
      tags:
      - Games
      operationId: submitAction
      summary: Execute authoritative action
      responses:
        '200':
          description: Execute authoritative action
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ActionResult'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ActionRequest'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - $ref: '#/components/parameters/csrf'
  /games/{gameId}/events:
    get:
      tags:
      - Games
      operationId: getEvents
      summary: List accepted events
      responses:
        '200':
          description: List accepted events
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GameEvent'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - name: after
        in: query
        schema:
          type: integer
          minimum: 0
      - name: limit
        in: query
        schema:
          type: integer
          minimum: 1
          maximum: 100
          default: 50
  /games/{gameId}/realtime-grant:
    post:
      tags:
      - Games
      operationId: realtimeGrant
      summary: Authorize temporary game Broadcast subscription
      responses:
        '200':
          description: Authorize temporary game Broadcast subscription
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RealtimeGrant'
        '401':
          description: Unauthenticated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: Conflict
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          description: Rate limited
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
      parameters:
      - $ref: '#/components/parameters/gameId'
      - $ref: '#/components/parameters/csrf'
components:
  securitySchemes:
    cookieSession:
      type: apiKey
      in: cookie
      name: bgwq_session
  parameters:
    definitionId:
      name: definitionId
      in: path
      required: true
      schema: &id001
        type: string
        format: uuid
    version:
      name: version
      in: path
      required: true
      schema:
        type: integer
        minimum: 1
    assetId:
      name: assetId
      in: path
      required: true
      schema: *id001
    gameId:
      name: gameId
      in: path
      required: true
      schema: *id001
    csrf:
      name: X-CSRF-Token
      in: header
      required: true
      schema: &id002
        type: string
  schemas:
    Error:
      type: object
      additionalProperties: false
      required:
      - code
      - message
      - request_id
      properties:
        code: *id002
        message: *id002
        request_id: *id001
        details:
          type: object
          additionalProperties: true
    Credentials:
      type: object
      additionalProperties: false
      required:
      - email
      - password
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
    Profile:
      type: object
      additionalProperties: false
      required:
      - id
      - display_name
      - anonymous
      properties:
        id: *id001
        display_name: *id002
        anonymous:
          type: boolean
        username:
          anyOf:
          - *id002
          - type: 'null'
    ProfilePatch:
      type: object
      additionalProperties: false
      required: []
      properties:
        display_name: *id002
        username:
          anyOf:
          - *id002
          - type: 'null'
    Session:
      type: object
      additionalProperties: false
      required:
      - authenticated
      - csrf_token
      properties:
        authenticated:
          type: boolean
        csrf_token: *id002
        profile:
          anyOf:
          - $ref: '#/components/schemas/Profile'
          - type: 'null'
    Definition:
      type: object
      additionalProperties: false
      required:
      - id
      - key
      - name
      - built_in
      - version
      - minimum_participants
      - maximum_participants
      properties:
        id: *id001
        key: *id002
        name: *id002
        built_in:
          type: boolean
        version: &id003
          type: integer
        minimum_participants: *id003
        maximum_participants: *id003
        description:
          anyOf:
          - *id002
          - type: 'null'
    DefinitionCreate:
      type: object
      additionalProperties: false
      required:
      - key
      - name
      properties:
        key: *id002
        name: *id002
        description: *id002
    ActionArgument:
      type: object
      additionalProperties: false
      required:
      - key
      - type
      - required
      properties:
        key: *id002
        type: *id002
        required:
          type: boolean
        choices:
          type: array
          items:
            type:
            - string
            - number
            - integer
            - boolean
            - 'null'
    AvailableAction:
      type: object
      additionalProperties: false
      required:
      - key
      - source_entity
      - parameters
      properties:
        key: *id002
        source_entity: *id001
        parameters:
          type: array
          items:
            $ref: '#/components/schemas/ActionArgument'
    Entity:
      type: object
      additionalProperties: false
      required:
      - id
      - type
      - kind
      - values
      properties:
        id: *id001
        type: *id002
        kind:
          enum:
          - game
          - space
          - item
          - objective
        owner:
          anyOf:
          - *id001
          - type: 'null'
        parent:
          anyOf:
          - *id001
          - type: 'null'
        location:
          anyOf:
          - *id001
          - type: 'null'
        values:
          type: object
          additionalProperties:
            type:
            - boolean
            - integer
            - number
            - string
            - 'null'
    Participant:
      type: object
      additionalProperties: false
      required:
      - id
      - user_id
      - role
      - seat
      - eliminated
      properties:
        id: *id001
        user_id: *id001
        role: *id002
        seat: *id003
        eliminated:
          type: boolean
    GameCreate:
      type: object
      additionalProperties: false
      required:
      - definition_id
      - version
      - idempotency_key
      - target_participants
      properties:
        definition_id: *id001
        version: *id003
        idempotency_key: *id002
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
    GameSummary:
      type: object
      additionalProperties: false
      required:
      - id
      - status
      - revision
      - definition
      - target_participants
      properties:
        id: *id001
        status:
          enum:
          - pending
          - active
          - finished
          - expired
        revision: *id003
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
        definition:
          $ref: '#/components/schemas/Definition'
    Game:
      type: object
      additionalProperties: false
      required:
      - id
      - status
      - revision
      - definition
      - target_participants
      - participants
      - entities
      - available_actions
      - server_time
      - outcomes
      properties:
        id: *id001
        status:
          enum:
          - pending
          - active
          - finished
          - expired
        revision: *id003
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
        definition:
          $ref: '#/components/schemas/Definition'
        participants:
          type: array
          items:
            $ref: '#/components/schemas/Participant'
        entities:
          type: array
          items:
            $ref: '#/components/schemas/Entity'
        available_actions:
          type: array
          items:
            $ref: '#/components/schemas/AvailableAction'
        server_time: &id004
          type: string
          format: date-time
        outcomes:
          type: array
          description: Empty until the game is finished. Every participant has one outcome when finished.
          items:
            $ref: '#/components/schemas/GameOutcome'
    Invitation:
      type: object
      additionalProperties: false
      required:
      - game_id
      - status
      - expires_at
      - definition
      - target_participants
      properties:
        game_id: *id001
        status:
          enum:
          - pending
          - active
          - expired
        expires_at: *id004
        target_participants:
          type: integer
          minimum: 2
          maximum: 64
        definition:
          $ref: '#/components/schemas/Definition'
    JoinRequest:
      type: object
      additionalProperties: false
      required:
      - idempotency_key
      properties:
        idempotency_key: *id002
    Command:
      type: object
      additionalProperties: false
      required:
      - key
      - source_entity
      - parameters
      properties:
        key: *id002
        source_entity: *id001
        parameters:
          type: object
          additionalProperties: true
    ActionRequest:
      type: object
      additionalProperties: false
      required:
      - expected_revision
      - action_id
      - action
      properties:
        expected_revision:
          type: integer
          minimum: 0
        action_id: *id002
        action:
          $ref: '#/components/schemas/Command'
    GameEvent:
      type: object
      additionalProperties: false
      required:
      - id
      - revision
      - kind
      - occurred_at
      properties:
        id: *id001
        revision: *id003
        kind: *id002
        occurred_at: *id004
    ActionResult:
      type: object
      additionalProperties: false
      required:
      - revision
      - game
      - event
      properties:
        revision: *id003
        game:
          $ref: '#/components/schemas/Game'
        event:
          $ref: '#/components/schemas/GameEvent'
    Rating:
      type: object
      additionalProperties: false
      required:
      - definition_id
      - rating
      - games
      properties:
        definition_id: *id001
        rating: *id003
        games: *id003
    Award:
      type: object
      additionalProperties: false
      required:
      - game_id
      - objective_entity_id
      - points
      properties:
        game_id: *id001
        objective_entity_id: *id001
        points: *id003
    AssetUploadRequest:
      type: object
      additionalProperties: false
      required:
      - key
      - mime
      - bytes
      - sha256
      properties:
        key: *id002
        mime:
          enum:
          - image/png
          - image/webp
        bytes:
          type: integer
          minimum: 1
          maximum: 2097152
        sha256:
          type: string
          pattern: ^[a-f0-9]{64}$
    AssetUpload:
      type: object
      additionalProperties: false
      required:
      - asset_id
      - upload_url
      - expires_at
      properties:
        asset_id: *id001
        upload_url:
          type: string
          format: uri
        expires_at: *id004
    Asset:
      type: object
      additionalProperties: false
      required:
      - id
      - key
      - mime
      - bytes
      - sha256
      properties:
        id: *id001
        key: *id002
        mime: *id002
        bytes: *id003
        sha256: *id002
    RealtimeGrant:
      type: object
      additionalProperties: false
      required:
      - topic
      - token
      - expires_at
      properties:
        topic: *id002
        token: *id002
        expires_at: *id004
    ConfigDocument:
      title: BoardGamesWithQuests portable configuration v1
      description: Versioned, portable authoring format; database stores its normalized relational
        projection.
      type: object
      additionalProperties: false
      required:
      - format
      - format_version
      - definition
      - roles
      - phases
      - entities
      - seeds
      - links
      - fields
      - actions
      - visuals
      - assets
      properties:
        format:
          const: bgwq.configuration
        format_version:
          const: 1
        definition:
          type: object
          additionalProperties: false
          required:
          - key
          - name
          - min_participants
          - max_participants
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
              minLength: 1
            description:
              type: string
            min_participants:
              type: integer
              minimum: 1
              maximum: 64
            max_participants:
              type: integer
              minimum: 1
              maximum: 64
            semantics_version:
              const: 1
        roles:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/role'
        phases:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/phase'
        entities:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/entity'
        seeds:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/seed'
        links:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/link'
        fields:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/field'
        actions:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/action'
        visuals:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/visual'
        assets:
          type: array
          items:
            $ref: '#/components/schemas/ConfigDocument/$defs/asset'
      $defs:
        key:
          type: string
          pattern: ^[a-z][a-z0-9_.-]*$
        role:
          type: object
          required:
          - key
          - name
          - min
          - max
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
            min:
              type: integer
              minimum: 0
            max:
              type: integer
              minimum: 0
            forward_row:
              type:
              - integer
              - 'null'
              enum:
              - -1
              - 1
              - null
              description: Optional forward row orientation used by generic relative-vector operations.
        phase:
          type: object
          required:
          - key
          - name
          - initial
          - order
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
            initial:
              type: boolean
            order:
              type: integer
        entity:
          type: object
          required:
          - key
          - kind
          - name
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            kind:
              enum:
              - game
              - space
              - item
              - objective
            name:
              type: string
        seed:
          type: object
          required:
          - key
          - type
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            type:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            owner:
              type: integer
              minimum: 0
            parent:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            location:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            order:
              type: integer
            row:
              type: integer
            column:
              type: integer
            x:
              type: number
            y:
              type: number
            values:
              type: object
              additionalProperties:
                $ref: '#/components/schemas/ConfigDocument/$defs/value'
        link:
          type: object
          required:
          - source
          - target
          - relation
          additionalProperties: false
          properties:
            source:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            target:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            relation:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            order:
              type: integer
        field:
          type: object
          required:
          - entity
          - key
          - type
          additionalProperties: false
          properties:
            entity:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            type:
              enum:
              - bool
              - int
              - decimal
              - text
              - instant
              - entity
              - participant
            nullable:
              type: boolean
            default:
              $ref: '#/components/schemas/ConfigDocument/$defs/value'
        value:
          type:
          - boolean
          - integer
          - number
          - string
          - 'null'
        expression:
          type: object
          required:
          - op
          additionalProperties: false
          properties:
            op:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            args:
              type: object
              additionalProperties:
                anyOf:
                - $ref: '#/components/schemas/ConfigDocument/$defs/expression'
                - type: array
                  items:
                    $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            value:
              $ref: '#/components/schemas/ConfigDocument/$defs/value'
            ref:
              type: string
            type:
              type: string
        effect:
          type: object
          required:
          - op
          additionalProperties: false
          properties:
            op:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            when:
              $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            args:
              type: object
              additionalProperties:
                anyOf:
                - $ref: '#/components/schemas/ConfigDocument/$defs/expression'
                - type: array
                  items:
                    $ref: '#/components/schemas/ConfigDocument/$defs/expression'
        action:
          type: object
          required:
          - key
          - entity
          - trigger
          - phase
          - condition
          - effects
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            entity:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            name:
              type: string
            trigger:
              enum:
              - command
              - hook
            hook:
              type: string
            phase:
              type: string
            parameters:
              type: array
              items:
                type: object
                required:
                - key
                - type
                additionalProperties: false
                properties:
                  key:
                    $ref: '#/components/schemas/ConfigDocument/$defs/key'
                  type:
                    type: string
                  required:
                    type: boolean
                  choices:
                    type: array
                    minItems: 1
                    uniqueItems: true
                    items:
                      type: string
            iterator:
              $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            variable:
              type: string
            condition:
              $ref: '#/components/schemas/ConfigDocument/$defs/expression'
            effects:
              type: array
              items:
                $ref: '#/components/schemas/ConfigDocument/$defs/effect'
            priority:
              type: integer
        visual:
          type: object
          required:
          - entity
          - primitives
          additionalProperties: false
          properties:
            entity:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            primitives:
              type: array
              items:
                type: object
                required:
                - kind
                additionalProperties: false
                properties:
                  kind:
                    enum:
                    - rectangle
                    - ellipse
                    - line
                    - path
                    - text
                    - image
                  x:
                    type: number
                  y:
                    type: number
                  width:
                    type: number
                  height:
                    type: number
                  fill:
                    type: string
                  stroke:
                    type: string
                  d:
                    type: string
                  text:
                    type: string
                  asset:
                    type: string
                  layer:
                    type: integer
        asset:
          type: object
          required:
          - key
          - mime
          - sha256
          - base64
          additionalProperties: false
          properties:
            key:
              $ref: '#/components/schemas/ConfigDocument/$defs/key'
            mime:
              enum:
              - image/png
              - image/webp
            sha256:
              type: string
              pattern: ^[0-9a-f]{64}$
            base64:
              type: string
    GameOutcome:
      type: object
      additionalProperties: false
      required:
      - participant_id
      - kind
      - score
      description: Immutable, participant-scoped settlement written atomically with the terminal
        accepted event.
      properties:
        participant_id:
          type: string
          format: uuid
        kind:
          type: string
          enum:
          - win
          - loss
          - draw
          - eliminated
        score:
          type: integer
          format: int64
```
