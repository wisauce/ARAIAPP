# Android Software Specification — Indoor AR Navigation MVP

Version: 2.0

Scope: one building floor, Android only. The visitor sets a start position on the floor plan. ARCore tracks movement from that position and the app draws the route in AR and on a 2D map.

This version is the implementation specification. It does not include a command-line prototype, a captured dataset, visual localization, or a visual-map processing pipeline.

## 1. Product scope

The system contains:

1. An Android application with map-manager mode and visitor-navigation mode.
2. A backend API that stores venues, floor geometry, destinations, and the route graph.
3. Object storage for the floor-plan image.

The visitor never uploads camera frames. The phone recognizes nothing about the building. Localization is the position and facing direction the visitor confirms on the map. ARCore then tracks motion until tracking is lost, at which point the visitor confirms position again.

### In scope

- Manager sign-in, one venue, one floor.
- Floor-plan image upload, scale calibration, walkable areas, obstacles, destinations, and a route graph.
- Publish an immutable map version.
- Visitor opens a published venue with no account.
- Visitor sets position and facing, searches a destination, and receives a route.
- On-device A* routing.
- AR turn cues while ARCore is tracking, plus a 2D map at all times.
- Temporary corridor closures.
- 2D-only fallback when ARCore or the camera is unavailable.

### Out of scope

- Command-line tools and feasibility prototypes.
- Datasets, frame dumps, and offline accuracy studies.
- Visual localization, image retrieval, local features, PnP, and sparse reconstruction.
- Mapping-session capture, alignment points, and visual-coverage reports.
- QR codes, Bluetooth beacons, indoor GPS, and dedicated 360° cameras.
- Multi-floor navigation and automatic emergency evacuation.
- Voice guidance.
- Automatic floor-geometry extraction. The manager draws the map.
- Visitor accounts, social features, and analytics dashboards.

## 2. Platform requirements

### Supported devices

- Android 10 or newer.
- `minSdk = 29`.
- Current Google Play-required target SDK.
- ARCore-certified device for AR mode.
- Rear-facing camera, gyroscope, and accelerometer for AR mode.
- Internet connection to download or refresh a published map. Routing and AR after that download work offline until the visitor picks another map version.

Before entering AR mode, the application must:

1. Check whether ARCore is supported.
2. Request ARCore installation or update when necessary.
3. Verify camera permission.
4. Fall back to the 2D map if AR is unavailable. The 2D route remains fully usable.

### Android technology stack

- Kotlin.
- Jetpack Compose.
- Coroutines and Flow.
- Hilt.
- ARCore SDK.
- Filament for AR rendering.
- Room.
- Retrofit and OkHttp.
- Kotlin Serialization.
- Gradle Kotlin DSL.
- DataStore for the manager access token.

Do not run CameraX concurrently with an ARCore session. ARCore owns the camera while its session is active.

Do not add Media3, WorkManager, or an image-processing module. The only upload is the floor-plan file, sent once through the API.

## 3. Android permissions

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<uses-feature
    android:name="android.hardware.camera.ar"
    android:required="false" />
```

`android.hardware.camera.ar` is not required, because the 2D map must install and run on devices without ARCore.

Location and storage permissions are not required. The manager picks a floor-plan file through the Storage Access Framework.

Camera permission explanation:

> The camera is used to show navigation arrows over the corridor. Your video is not recorded or uploaded.

If the visitor denies the camera permission, stay on the 2D map and do not ask again until they open AR mode.

## 4. Application roles

### Map manager

Authenticated user who can:

- Create a venue.
- Upload a floor-plan image.
- Calibrate scale.
- Draw walkable areas and obstacles.
- Place destinations, route nodes, and route edges.
- Mark an edge temporarily closed.
- Publish a map version.

### Visitor

Unauthenticated user who can:

- Open a published venue.
- Set a start position and facing direction on the floor plan.
- Search destinations.
- Follow the route on the 2D map and, when AR is available, in the camera view.
- Set the position again when tracking is lost.

## 5. Android project structure

```text
app/
core-model/
core-routing/
core-network/
core-database/
core-ui/
core-ar/
feature-auth/
feature-venue/
feature-floor-editor/
feature-navigation/
```

`core-model` and `core-routing` are plain Kotlin. They must not depend on Android, ARCore, or the network.

Each feature uses:

```text
Compose UI
    ↓
ViewModel
    ↓
Use cases
    ↓
Repository interface
    ↓
Local and remote data sources
```

Unidirectional state:

```kotlin
data class ScreenState(...)
sealed interface ScreenAction
sealed interface ScreenEffect
```

Module responsibilities:

| Module | Responsibility |
| --- | --- |
| `core-model` | Venue, floor, destination, graph, pose, and map-version types |
| `core-routing` | Polygon tests, graph checks, and A* |
| `core-network` | Retrofit API and DTO mapping |
| `core-database` | Room cache of the published map package |
| `core-ui` | Shared map canvas, dialogs, and error states |
| `core-ar` | ARCore session, floor-to-session transform, and arrow anchors |
| `feature-auth` | Manager login and token storage |
| `feature-venue` | Venue list and create |
| `feature-floor-editor` | Calibration, geometry, destinations, graph, publish |
| `feature-navigation` | Visitor pin, search, 2D route, and AR route |

## 6. Screens

### Shared

- Launch and compatibility check.
- Venue selection.
- Camera permission explanation, shown only when entering AR.
- Network error with retry.
- AR-unavailable notice that leaves the 2D map in place.

### Manager

1. Sign in.
2. Venue list and create venue.
3. Floor-plan upload.
4. Scale calibration.
5. Walkable-area and obstacle editor.
6. Destination editor.
7. Route-graph editor.
8. Closure toggle on an existing edge.
9. Publish confirmation.

There is no mapping-capture screen, processing-status screen, or visual-coverage report.

### Visitor

1. Venue details, including map version.
2. Set position and facing.
3. Destination search.
4. Route preview on the 2D map.
5. AR navigation.
6. Tracking-lost recovery, which returns to set position.
7. Arrival.

## 7. Domain model

Floor-plan coordinates are metres:

```text
Origin: lower-left corner of the floor image
X axis: right
Y axis: up
Z axis: vertical
Floor level: Z = 0
```

Yaw is radians, `0` along +X, increasing counter-clockwise toward +Y. It is the visitor's facing direction projected onto the floor.

```kotlin
data class Venue(
    val id: String,
    val name: String,
    val publishedVersion: Int?
)

data class FloorMap(
    val id: String,
    val venueId: String,
    val version: Int,
    val status: MapStatus,
    val widthMeters: Double,
    val heightMeters: Double,
    val imageUrl: String,
    val walkableAreas: List<Polygon2D>,
    val obstacles: List<Polygon2D>,
    val destinations: List<Destination>,
    val routeNodes: List<RouteNode>,
    val routeEdges: List<RouteEdge>
)

enum class MapStatus {
    DRAFT,
    PUBLISHED,
    ARCHIVED
}

data class Polygon2D(
    val id: String,
    val points: List<Point2D>
)

data class Point2D(
    val x: Double,
    val y: Double
)

data class Destination(
    val id: String,
    val name: String,
    val x: Double,
    val y: Double,
    val nodeId: String
)

data class RouteNode(
    val id: String,
    val x: Double,
    val y: Double,
    val type: NodeType
)

enum class NodeType {
    INTERSECTION,
    DOOR,
    ENDPOINT
}

data class RouteEdge(
    val id: String,
    val fromNodeId: String,
    val toNodeId: String,
    val distanceMeters: Double,
    val accessible: Boolean,
    val temporarilyClosed: Boolean
)

data class StartPose(
    val x: Double,
    val y: Double,
    val yawRadians: Double
)
```

`distanceMeters` is the Euclidean length of the edge and is computed by the server when the graph is saved. The client recomputes it for display and does not trust a hand-edited length.

A destination is a labeled point snapped to a `DOOR` node. The visitor is routed to that node, not to the room center.

The published package downloaded by the visitor is the `FloorMap` plus the floor-plan image bytes. Draft geometry is visible only to the manager.

## 8. Floor editor

The manager can:

- Pan and zoom the floor image.
- Calibrate scale.
- Draw, move, and delete walkable polygons and obstacle polygons.
- Place, name, move, and delete destinations.
- Place route nodes and connect them with edges.
- Toggle `accessible` and `temporarilyClosed` on an edge.
- Undo the latest geometry edit in the current editor session.

Scale calibration:

1. The manager draws a line between two points on the image.
2. The manager enters the real distance in metres, which must be greater than 0.
3. The app sets `widthMeters` and `heightMeters` from that scale and the image aspect ratio.
4. Saving geometry before calibration is rejected.

Polygon rules:

- A polygon has at least 3 points.
- Edges must not self-intersect.
- An obstacle may lie inside a walkable polygon.
- A destination point must lie inside some walkable polygon and outside every obstacle.

Graph rules, enforced before publish:

- Every edge references two existing nodes.
- Duplicate edges in the same direction are rejected. The opposite direction is a separate edge, so the graph is directed.
- Every destination references a node within 1.0 metre of its point.
- Every destination node can be reached from at least one other node, or the destination node is allowed to be a dead end only if some edge arrives there.
- `distanceMeters` is recalculated from node coordinates on every save.

Publish is enabled only when calibration, at least one walkable polygon, at least one destination, and the graph rules all pass. Publishing copies the draft into a new immutable version and increments `version`. Further edits create the next draft and do not change the published version.

Closing a corridor sets `temporarilyClosed = true` on that edge and publishes a new version. The visitor keeps the version they already downloaded until they refresh.

## 9. Visitor position

This is the only localization mechanism.

1. The visitor opens the published floor plan.
2. They tap a point inside a walkable area, outside obstacles. Taps outside walkable space are rejected.
3. They drag in the direction they are facing, or rotate a facing control. The control shows an arrow on the map.
4. They confirm. That confirmation is `StartPose`.
5. If AR mode starts, the app reads the ARCore camera pose at the confirmation frame and computes the floor-to-session transform in section 11.
6. The 2D map draws the visitor at `StartPose` immediately, even when AR is off.

Changing position, including after tracking loss, replaces `StartPose` and rebuilds the transform. The route is recalculated from the new point.

The route starts at the nearest graph node to `StartPose` if that node lies inside the same walkable polygon and the straight line between them does not cross an obstacle. Otherwise the app shows "Move the pin onto a corridor" and does not start navigation.

## 10. Routing

`core-routing` runs on the device against the cached published graph.

```kotlin
fun findRoute(
    map: FloorMap,
    start: Point2D,
    destinationId: String,
    requireAccessible: Boolean
): RouteResult
```

```kotlin
sealed interface RouteResult {
    data class Found(val nodeIds: List<String>, val distanceMeters: Double) : RouteResult
    data object StartOffGraph : RouteResult
    data object DestinationMissing : RouteResult
    data object Unreachable : RouteResult
}
```

Algorithm: A* on directed edges. Heuristic is Euclidean distance to the destination node. An edge is usable when `temporarilyClosed` is false and, if `requireAccessible` is true, `accessible` is true.

The start is attached to the nearest eligible node as a temporary edge of Euclidean length. The destination is its linked node. The returned path includes that start node and the destination node.

Before displaying a route:

- The map `status` is `PUBLISHED`.
- The destination exists on that version.
- Every path segment between consecutive nodes lies inside the union of walkable polygons and outside obstacles. If a graph segment fails this check, skip that edge during search. If the destination becomes unreachable, return `Unreachable`.

The accessible toggle is a filter on the visitor route preview, default off.

Route calculation for a single floor must finish on the device in under 100 milliseconds for a graph of up to 500 nodes.

## 11. Coordinate transformation

Define:

```text
T_A_B = transformation of coordinates from B into A
```

At confirmation:

- `StartPose` defines the visitor position on the floor and the facing yaw.
- ARCore supplies `T_session_camera` for the confirmation frame.
- The app builds `T_floor_camera` from `StartPose` and a fixed eye height of 1.5 metres. Pitch and roll at confirmation are taken from ARCore so the floor stays horizontal in the session; yaw is taken from `StartPose`.

```text
T_floor_session = T_floor_camera × inverse(T_session_camera)
```

For an object defined in floor coordinates:

```text
T_session_object = inverse(T_floor_session) × T_floor_object
```

Store the transform in double precision. Convert to rendering matrices only at the graphics boundary.

After confirmation, the visitor position used by the 2D map is the floor-space transform of the current ARCore camera pose, with Z discarded. While AR is off, the 2D position stays at the last confirmed `StartPose` and does not drift.

Do not animate a correction across frames. A new confirmation replaces the transform on the next frame. AR cues hide during that replacement and reappear once the new anchors exist.

## 12. Tracking

After a confirmed start, while AR mode is on:

1. ARCore tracks at the device frame rate.
2. The app keeps `T_floor_session` until the visitor sets position again or tracking is lost.
3. There is no background relocalization and no periodic server request.

```text
MAP_ONLY
→ SETTING_POSITION
→ ROUTE_PREVIEW
→ NAVIGATING
→ ARRIVED

NAVIGATING → TRACKING_LOST
TRACKING_LOST → SETTING_POSITION
```

- `MAP_ONLY`: 2D map, no AR session. Entered when ARCore is missing, the camera is denied, or the visitor closes AR.
- `SETTING_POSITION`: the visitor is placing the pin and facing arrow.
- `ROUTE_PREVIEW`: a route exists and AR has not started, or AR is ready and waiting for the visitor to tap Start.
- `NAVIGATING`: AR session is running, tracking state is `TRACKING`, and arrows are visible.
- `TRACKING_LOST`: ARCore reports `PAUSED` or `STOPPED`, or tracking has been anything other than `TRACKING` for 1 second continuously. Hide arrows. The 2D map remains on the last good floor position.
- `ARRIVED`: the visitor's floor position is within 2.0 metres of the destination node. Show arrival and stop arrows.

AR arrows are displayed only in `NAVIGATING`.

Leaving the navigation screen pauses the ARCore session. Returning does not reuse the old transform; the visitor sets position again.

## 13. AR rendering

Display only:

- One turn arrow at the next node where the path heading changes by more than 25 degrees.
- On a straight run longer than 8 metres, one forward marker halfway to the next turn, replaced as the visitor passes it.
- Remaining distance in metres, as a text overlay in screen space.
- A destination marker when the destination node is within 15 metres.

Do not place a chain of arrows along the corridor.

AR objects:

- Are anchored in floor coordinates at Z = 0.05 metres so they sit just above the floor.
- Are hidden outside `NAVIGATING`.
- Are not updated from a stale pose after tracking loss.
- Must not cover the whole camera view. Arrows stay small relative to the corridor.

The 2D map stays available on the same screen, collapsed to a corner, and expands when the visitor taps it. Expanding the map does not stop the AR session until the visitor leaves navigation or sets a new position.

Target: the AR view sustains at least 30 FPS on an ARCore-certified device while one route is shown. Camera handling and anchor updates stay off the main thread except for the Filament frame submission ARCore requires.

## 14. Local storage

Room tables:

```text
venues
map_packages
destinations
route_nodes
route_edges
walkable_areas
obstacles
```

`map_packages` stores `venueId`, `version`, `widthMeters`, `heightMeters`, image file path, and `downloadedAt`.

Cache the published package only. Replace it when the visitor refreshes and the server version is newer. Do not merge a new version into an in-progress navigation session; finish or cancel navigation, then swap the package.

Do not store camera images, AR frames, or manager tokens in Room. The manager token lives in DataStore and is cleared on sign-out.

## 15. Backend API

Base path `/v1`. JSON bodies use Kotlin Serialization field names as documented below. Errors use:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Scale has not been calibrated."
}
```

HTTP status: `400` validation, `401` unauthenticated manager route, `403` wrong role, `404` missing resource, `409` publish conflict.

### Auth

Manager routes require `Authorization: Bearer <accessToken>`. Visitor routes do not.

```http
POST /v1/auth/login
```

```json
{ "email": "manager@example.com", "password": "secret" }
```

```json
{ "accessToken": "<jwt>", "expiresInSeconds": 3600 }
```

Tokens expire. There is no refresh token in the MVP. A `401` returns the manager to sign in.

### Venues

```http
POST /v1/venues
{ "name": "Main building" }
```

```json
{ "id": "ven_1", "name": "Main building", "publishedVersion": null }
```

```http
GET /v1/venues
GET /v1/venues/{venueId}
```

`GET /v1/venues` is public and returns only venues with a published version. `GET /v1/venues/{venueId}` is public for published fields and includes `publishedVersion`. The draft is not included.

### Floor plan

```http
POST /v1/venues/{venueId}/floor-plan
Content-Type: multipart/form-data
file: PNG or JPEG, maximum 15 MB
```

The server stores the file and creates or replaces the current draft image. It does not accept PDF. Response:

```json
{
  "floorId": "flr_1",
  "imageUrl": "https://cdn.example/flr_1.png",
  "widthPixels": 4000,
  "heightPixels": 2500
}
```

`widthMeters` and `heightMeters` stay unset until calibration is saved.

### Geometry

```http
PUT /v1/floors/{floorId}/draft
```

Body is the draft `FloorMap` fields the manager edits: `widthMeters`, `heightMeters`, polygons, destinations, nodes, and edges. The server:

- Rejects the body when scale is missing or any rule in section 8 fails.
- Recomputes `distanceMeters`.
- Saves the draft. Status stays `DRAFT`.

```http
GET /v1/floors/{floorId}/draft
```

Manager only. Returns the current draft.

### Publish and read

```http
POST /v1/floors/{floorId}/publish
```

Creates the next published version from the draft. Response is the published `FloorMap`. A second publish with no draft changes returns `409`.

```http
GET /v1/venues/{venueId}/published-map
```

Public. Returns the latest published `FloorMap` and a downloadable `imageUrl`.

```http
POST /v1/floors/{floorId}/edges/{edgeId}/closure
{ "temporarilyClosed": true }
```

Manager only. Updates the draft edge, then publishes a new version in the same request so visitors can refresh to a closed corridor. Response is the new published `FloorMap`.

There are no localization, mapping-session, frame, or alignment endpoints.

## 16. Backend infrastructure

```text
FastAPI
PostgreSQL with PostGIS
S3-compatible object storage for floor-plan images
```

One API process is enough. There is no worker queue, Redis, or GPU service.

Map versions are immutable rows. The visitor response always includes `version`. The app pins navigation to that version until the visitor leaves the venue or explicitly refreshes.

Suggested tables: `users`, `venues`, `floor_versions`, `destinations`, `route_nodes`, `route_edges`, `polygons`. Polygons and points are stored as PostGIS geometry in the floor coordinate system, SRID unset, units metres.

## 17. Security and privacy

- TLS on every connection.
- Manager passwords stored with a slow hash.
- Short-lived bearer tokens.
- Manager routes reject missing or expired tokens.
- Visitors can read published maps only.
- Floor-plan object URLs are unguessable or signed.
- Camera frames stay on the device and are never written to disk by the app, uploaded, or logged.
- Do not log tokens, passwords, or image URLs.
- Sign-out deletes the local token.
- Deleting a venue deletes its drafts, published versions, and floor-plan objects.

No face detection pipeline is required, because no camera image is retained.

## 18. Performance and acceptance

The MVP is done when all of the following are true:

1. A manager can sign in, create a venue, upload a PNG or JPEG plan, calibrate scale, draw a walkable corridor, place two destinations, connect a graph, and publish.
2. A visitor can open that venue with no account, download the package, set a pin and facing direction, search a destination, and see a 2D route.
3. On an ARCore device, Start opens the camera and shows a single turn arrow that moves with the phone as the phone is carried along the corridor.
4. Denying the camera, or running on a device without ARCore, still shows the 2D route.
5. After ARCore leaves `TRACKING` for 1 second, arrows disappear and the app asks the visitor to set position again.
6. Within 2 metres of the destination node, the app shows arrival.
7. Marking an edge closed publishes a new version. A visitor who refreshes no longer receives a route through that edge. A visitor who does not refresh keeps the previous route.
8. Route search returns `Unreachable` when closures or obstacles disconnect the destination, and the UI says the destination cannot be reached.
9. Unit tests cover coordinate transforms, A*, polygon rejection, publish validation, and the tracking state machine.
10. No screen, endpoint, or module exists for mapping capture, datasets, or visual localization.

Android targets:

- AR rendering at least 30 FPS during navigation.
- No camera work on the main thread beyond the ARCore frame callback.
- Published package preferably under 20 MB, dominated by the floor-plan image.
- The app survives process death on the 2D route screen by restoring the cached package, then requires the visitor to set position again before AR resumes.

## 19. Testing

### Unit tests (`core-model`, `core-routing`, `core-ar` transform math)

- Yaw and quaternion construction of `T_floor_camera`.
- Round trip of a floor point through `T_floor_session`.
- A* prefers the shorter directed path and ignores closed edges.
- Accessible filter excludes inaccessible edges.
- Self-intersecting polygons and out-of-area destinations fail validation.
- Destination snap rejects a node farther than 1.0 metre.
- Tracking transitions, including the 1 second loss timer and arrival at 2.0 metres.

### Instrumentation

- Camera permission denied, then 2D route still works.
- ARCore unavailable, then 2D route still works.
- Airplane mode after the package is cached, then route preview still works.
- Process death on the 2D route screen restores the map and clears the AR session.
- Rotation during AR navigation keeps the session orientation locked to the orientation in which the session started.

### Manual pass on one floor

Walk a published route in both directions on one ARCore phone. Confirm the turn arrow matches the next graph turn, arrival fires at the door, and setting the pin again after covering the camera resumes a sensible arrow. This pass checks the transform and the graph. It is not a dataset collection step.

## 20. Implementation sequence

Build in this order. Do not start a later step by stubbing an earlier one with a fake localization service.

1. `core-model` and `core-routing`, with unit tests, before any UI.
2. Backend auth, venues, floor-plan upload, draft save, and publish.
3. Android sign-in, venue list, and floor editor through publish.
4. Download and Room cache of the published package.
5. Visitor pin, facing control, destination search, and 2D route.
6. ARCore session, transform, and one turn arrow.
7. Tracking-loss recovery and arrival.
8. Edge closure and version refresh.
9. Permission, network, and process-death handling from section 19.

The first milestone is a published floor and a 2D route from a visitor pin. AR arrows come after that route is correct on the map.
