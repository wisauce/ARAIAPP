package com.araiap.core.network

import com.araiap.core.model.FloorMap
import com.araiap.core.model.Venue
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Part
import retrofit2.http.Path

@Serializable
data class CreateVenueRequest(val name: String)

@Serializable
data class ClosureRequest(val temporarilyClosed: Boolean)

@Serializable
data class FloorPlanResponse(
    val floorId: String,
    val imageUrl: String,
    val widthPixels: Int,
    val heightPixels: Int,
)

interface AraiapApi {
    @GET("venues")
    suspend fun venues(): List<Venue>

    @GET("venues/{id}")
    suspend fun venue(@Path("id") id: String): Venue

    @POST("venues")
    suspend fun createVenue(@Body request: CreateVenueRequest): Venue

    @Multipart
    @POST("venues/{id}/floor-plan")
    suspend fun uploadFloorPlan(
        @Path("id") id: String,
        @Part file: MultipartBody.Part,
    ): FloorPlanResponse

    @GET("floors/{id}/draft")
    suspend fun draft(@Path("id") id: String): FloorMap

    @PUT("floors/{id}/draft")
    suspend fun saveDraft(@Path("id") id: String, @Body map: FloorMap): FloorMap

    @POST("floors/{id}/publish")
    suspend fun publish(@Path("id") id: String): FloorMap

    @GET("venues/{id}/published-map")
    suspend fun publishedMap(@Path("id") id: String): FloorMap

    @POST("floors/{f}/edges/{e}/closure")
    suspend fun setClosure(
        @Path("f") floorId: String,
        @Path("e") edgeId: String,
        @Body request: ClosureRequest,
    ): FloorMap
}

object ApiFactory {
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        coerceInputValues = true
    }

    fun create(url: String): AraiapApi {
        require(url.startsWith("http://") || url.startsWith("https://"))
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val client = OkHttpClient.Builder().addInterceptor(logging).build()
        return Retrofit.Builder()
            .baseUrl(url)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(AraiapApi::class.java)
    }
}

sealed interface NetworkResult<out T> {
    data class Success<T>(val value: T) : NetworkResult<T>
    data class Failure(val status: Int?, val message: String) : NetworkResult<Nothing>
}

suspend fun <T> apiCall(block: suspend () -> T): NetworkResult<T> {
    return try {
        NetworkResult.Success(block())
    } catch (error: HttpException) {
        NetworkResult.Failure(error.code(), "Request failed.")
    } catch (error: Exception) {
        NetworkResult.Failure(null, error.message ?: "Network unavailable.")
    }
}

fun floorPlanPart(name: String, type: String, body: RequestBody): MultipartBody.Part {
    return MultipartBody.Part.createFormData("file", name, body)
}
