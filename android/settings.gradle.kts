pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
plugins { id("org.gradle.toolchains.foojay-resolver-convention") version "0.9.0" }
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}
rootProject.name = "Araiap"
include(":app", ":core-model", ":core-routing", ":core-network", ":core-database", ":core-ui", ":core-ar", ":feature-venue", ":feature-floor-editor", ":feature-navigation")
