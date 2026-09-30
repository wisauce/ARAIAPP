package com.araiap.core.ar
import android.app.Activity
import android.content.Context
import com.google.ar.core.*
import com.google.android.filament.Engine
import com.google.android.filament.EntityManager
enum class ArAvailability{READY,NEEDS_INSTALL,UNAVAILABLE}
class ArSessionController(private val context:Context):AutoCloseable{private var session:Session?=null
 fun availability():ArAvailability{val a=ArCoreApk.getInstance().checkAvailability(context);return when{a==ArCoreApk.Availability.SUPPORTED_NOT_INSTALLED||a==ArCoreApk.Availability.SUPPORTED_APK_TOO_OLD->ArAvailability.NEEDS_INSTALL;a.isSupported->ArAvailability.READY;else->ArAvailability.UNAVAILABLE}}
 fun requestInstall(a:Activity)=ArCoreApk.getInstance().requestInstall(a,true)
 fun resume(){val s=session?:Session(context).also{it.configure(Config(it).apply{planeFindingMode=Config.PlaneFindingMode.DISABLED;updateMode=Config.UpdateMode.LATEST_CAMERA_IMAGE});session=it};s.resume()}
 fun pause(){session?.pause()};fun update():ArFrame?{val f=session?.update()?:return null;val m=FloatArray(16);f.camera.pose.toMatrix(m,0);return ArFrame(Matrix4d.fromColumnMajor(m),when(f.camera.trackingState){TrackingState.TRACKING->CameraTracking.TRACKING;TrackingState.PAUSED->CameraTracking.PAUSED;TrackingState.STOPPED->CameraTracking.STOPPED})}
 override fun close(){session?.close();session=null}}
data class ArFrame(val sessionCamera:Matrix4d,val tracking:CameraTracking)
class FilamentCueTransform:AutoCloseable{private val engine=Engine.create();private val entity=EntityManager.get().create();private val instance:Int
 init{engine.transformManager.create(entity);instance=engine.transformManager.getInstance(entity)}
 fun update(m:Matrix4d){engine.transformManager.setTransform(instance,m.toFloatArrayColumnMajor())}
 override fun close(){engine.transformManager.destroy(entity);EntityManager.get().destroy(entity);engine.destroy()}}
