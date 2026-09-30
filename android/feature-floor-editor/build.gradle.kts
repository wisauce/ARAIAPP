plugins { alias(libs.plugins.android.library); alias(libs.plugins.kotlin.android); alias(libs.plugins.kotlin.compose); alias(libs.plugins.kapt); alias(libs.plugins.hilt) }
android {
    namespace = "com.araiap.feature.floor.editor"; compileSdk = 35
    defaultConfig { minSdk = 29 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
    
}
kapt { correctErrorTypes = true }
kotlin { jvmToolchain(21) }
dependencies { implementation(project(":core-model")); implementation(project(":core-routing"))
    implementation(project(":core-network")); implementation(project(":core-ui")); implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose); implementation(libs.hilt.android); kapt(libs.hilt.compiler); implementation(libs.hilt.navigation.compose)
    implementation(platform(libs.androidx.compose.bom)); implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui); implementation(libs.kotlinx.coroutines.android) }
