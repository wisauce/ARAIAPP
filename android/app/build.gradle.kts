plugins {
    alias(libs.plugins.android.application); alias(libs.plugins.kotlin.android); alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kapt); alias(libs.plugins.hilt)
}
android {
    namespace = "com.araiap.app"; compileSdk = 35
    defaultConfig {
        applicationId = "com.araiap.app"; minSdk = 29; targetSdk = 35; versionCode = 1; versionName = "1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "API_BASE_URL", "\"http://192.168.100.183:8000/v1/\"")
    }
    buildTypes {
        debug { isMinifyEnabled = false }
        release { isMinifyEnabled = true; proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro") }
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }; buildFeatures { compose = true; buildConfig = true }
}
kapt { correctErrorTypes = true }; kotlin { jvmToolchain(17) }
dependencies {
    implementation(project(":core-model")); implementation(project(":core-network")); implementation(project(":core-database"))
    implementation(project(":core-ui")); implementation(project(":core-ar"))
    implementation(project(":feature-venue")); implementation(project(":feature-floor-editor")); implementation(project(":feature-navigation"))
    implementation(libs.androidx.core.ktx); implementation(libs.androidx.activity.compose); implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.room.runtime); implementation(libs.hilt.android); kapt(libs.hilt.compiler); implementation(libs.hilt.navigation.compose)
    implementation(platform(libs.androidx.compose.bom)); implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3); implementation(libs.androidx.compose.ui.tooling.preview)
    debugImplementation(libs.androidx.compose.ui.tooling)
    testImplementation(libs.junit); androidTestImplementation(libs.androidx.test.junit)
    androidTestImplementation(libs.androidx.test.espresso); androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4); debugImplementation(libs.androidx.compose.ui.test.manifest)
}
