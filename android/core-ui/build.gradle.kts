plugins { alias(libs.plugins.android.library); alias(libs.plugins.kotlin.android); alias(libs.plugins.kotlin.compose) }
android {
    namespace = "com.araiap.core.ui"; compileSdk = 35
    defaultConfig { minSdk = 29 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
    
}

kotlin { jvmToolchain(21) }
dependencies { api(project(":core-model"))
    implementation(platform(libs.androidx.compose.bom)); implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.foundation); implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview); debugImplementation(libs.androidx.compose.ui.tooling) }
