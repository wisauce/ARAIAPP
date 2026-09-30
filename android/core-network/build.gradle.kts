plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
}
kotlin { jvmToolchain(21) }
dependencies {
    api(project(":core-model"))
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.retrofit.core)
    implementation(libs.retrofit.serialization)
    implementation(libs.okhttp.core)
    implementation(libs.okhttp.logging)
    testImplementation(libs.junit)
}
