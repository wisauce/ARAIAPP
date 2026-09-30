plugins { alias(libs.plugins.android.library); alias(libs.plugins.kotlin.android) }
android {
    namespace = "com.araiap.core.ar"; compileSdk = 35
    defaultConfig { minSdk = 29 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    
    testOptions { unitTests.isReturnDefaultValues = true }
}

kotlin { jvmToolchain(21) }
dependencies { api(project(":core-model")); implementation(libs.arcore)
    implementation(libs.filament.android); implementation(libs.filament.gltfio)
    implementation(libs.kotlinx.coroutines.android); testImplementation(libs.junit) }
