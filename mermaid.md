# Phone-to-server technical architecture

```mermaid
flowchart LR
    subgraph phone [Android phone]
        subgraph phoneUI [Compose features]
            managerUI[Manager editor]
            visitorUI[Visitor navigation]
        end

        subgraph phoneDomain [On-device domain]
            viewModels[ViewModels and use cases]
            repositories[Repositories]
            routeEngine["Geometry and A-star routing"]
            transformEngine[Floor and AR transforms]
            trackingState[Tracking state machine]
        end

        subgraph phonePlatform [Android platform]
            room[(Room published-map cache)]
            retrofit[Retrofit and OkHttp]
            arCore[ARCore motion tracking]
            filament[Filament AR rendering]
        end

        managerUI --> viewModels
        visitorUI --> viewModels
        viewModels --> repositories
        repositories <--> room
        repositories <--> retrofit
        room --> routeEngine
        visitorUI --> routeEngine
        visitorUI --> transformEngine
        arCore --> transformEngine
        transformEngine --> trackingState
        routeEngine --> filament
        transformEngine --> filament
        trackingState --> filament
    end

    subgraph transport [Phone and server boundary]
        publicContract["Public HTTPS and JSON<br/>venues and published maps"]
        managerContract["Manager HTTPS<br/>JSON and multipart image"]
        imageDownload["HTTPS floor-plan download"]
    end

    subgraph server [Backend server]
        reverseProxy[TLS termination]
        fastAPI[FastAPI application]

        subgraph serverModules [Application subsystems]
            publicRoutes[Public map routes]
            managerRoutes[Manager routes]
            validation["Scale, polygon and graph validation"]
            publisher[Immutable map publisher]
            storageAdapter[S3 storage adapter]
        end

        reverseProxy --> fastAPI
        fastAPI --> publicRoutes
        fastAPI --> managerRoutes
        managerRoutes --> validation
        managerRoutes --> publisher
        managerRoutes --> storageAdapter
        publicRoutes --> publisher
        publicRoutes --> storageAdapter
    end

    subgraph persistence [Server persistence]
        postgres[(PostgreSQL and PostGIS)]
        objectStore[(MinIO development or S3 production)]
    end

    retrofit <-->|GET public resources| publicContract
    retrofit <-->|Manager commands| managerContract
    room <-->|Floor-plan bytes| imageDownload
    publicContract <--> reverseProxy
    managerContract <--> reverseProxy
    imageDownload <--> objectStore

    validation <--> postgres
    publisher <--> postgres
    storageAdapter <--> objectStore
```

## What crosses the boundary

```mermaid
sequenceDiagram
    participant Phone as Android phone
    participant API as FastAPI server
    participant DB as PostgreSQL and PostGIS
    participant S3 as MinIO or S3

    Note over Phone,S3: Manager setup
    Phone->>API: Floor-plan PNG or JPEG
    API->>S3: Store floor-plan object
    API-->>Phone: Floor id, dimensions and image URL
    Phone->>API: Calibrated polygons, destinations, nodes and edges
    API->>API: Validate geometry and graph
    API->>DB: Save draft
    Phone->>API: Publish command
    API->>DB: Create immutable map version
    API-->>Phone: Published FloorMap JSON

    Note over Phone,S3: Visitor use
    Phone->>API: Request latest published map
    API->>DB: Read published version
    API-->>Phone: FloorMap JSON and image URL
    Phone->>S3: Download floor-plan image
    S3-->>Phone: Image bytes
    Note over Phone: Cache package, calculate route and track AR locally
    Note over Phone,API: No camera frames, AR poses or visitor routes are uploaded
```

The server is responsible for map validation, image storage, and immutable publishing. The phone is responsible for caching, route calculation, start-position confirmation, ARCore tracking, coordinate transforms, and rendering. The internal MVP has no credential subsystem.
