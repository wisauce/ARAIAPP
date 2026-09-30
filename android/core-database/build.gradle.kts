plugins { alias(libs.plugins.android.library); alias(libs.plugins.kotlin.android); alias(libs.plugins.kapt); alias(libs.plugins.hilt) }
android {
    namespace = "com.araiap.core.database"; compileSdk = 35
    defaultConfig { minSdk = 29 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    
    
}
kapt { correctErrorTypes = true }
kotlin { jvmToolchain(21) }
dependencies { api(project(":core-model"))
    implementation(libs.room.runtime); implementation(libs.room.ktx); implementation(libs.kotlinx.serialization.json)
    kapt(libs.room.compiler); implementation(libs.hilt.android); kapt(libs.hilt.compiler) }
