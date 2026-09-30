package com.araiap.core.ar
import com.araiap.core.model.*
import kotlin.math.*
data class Vector3d(val x:Double,val y:Double,val z:Double)
data class Quaterniond(val x:Double,val y:Double,val z:Double,val w:Double){
 operator fun times(o:Quaterniond)=Quaterniond(w*o.x+x*o.w+y*o.z-z*o.y,w*o.y-x*o.z+y*o.w+z*o.x,w*o.z+x*o.y-y*o.x+z*o.w,w*o.w-x*o.x-y*o.y-z*o.z)
 fun normalized():Quaterniond{val n=sqrt(x*x+y*y+z*z+w*w);return Quaterniond(x/n,y/n,z/n,w/n)}
 companion object{private fun axis(x:Double,y:Double,z:Double,a:Double)=Quaterniond(x*sin(a/2),y*sin(a/2),z*sin(a/2),cos(a/2));fun floorYawPitchRoll(yaw:Double,pitch:Double,roll:Double)=(axis(0.0,0.0,1.0,yaw)*axis(0.0,1.0,0.0,pitch)*axis(1.0,0.0,0.0,roll)).normalized()}
}
class Matrix4d private constructor(private val v:DoubleArray){
 operator fun times(o:Matrix4d):Matrix4d{val r=DoubleArray(16);for(i in 0..3)for(j in 0..3)r[i*4+j]=(0..3).sumOf{v[i*4+it]*o.v[it*4+j]};return Matrix4d(r)}
 fun transform(p:Vector3d):Vector3d{val x=v[0]*p.x+v[1]*p.y+v[2]*p.z+v[3];val y=v[4]*p.x+v[5]*p.y+v[6]*p.z+v[7];val z=v[8]*p.x+v[9]*p.y+v[10]*p.z+v[11];return Vector3d(x,y,z)}
 fun inverseRigid():Matrix4d{val r=identity().v;for(i in 0..2)for(j in 0..2)r[i*4+j]=v[j*4+i];val t=Vector3d(v[3],v[7],v[11]);r[3]=-(r[0]*t.x+r[1]*t.y+r[2]*t.z);r[7]=-(r[4]*t.x+r[5]*t.y+r[6]*t.z);r[11]=-(r[8]*t.x+r[9]*t.y+r[10]*t.z);return Matrix4d(r)}
 fun toFloatArrayColumnMajor()=FloatArray(16){v[(it%4)*4+it/4].toFloat()}
 companion object{fun identity()=Matrix4d(doubleArrayOf(1.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0));fun rigid(t:Vector3d,r:Quaterniond):Matrix4d{val q=r.normalized();val x=q.x;val y=q.y;val z=q.z;val w=q.w;return Matrix4d(doubleArrayOf(1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y),t.x,2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x),t.y,2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y),t.z,0.0,0.0,0.0,1.0))};fun fromColumnMajor(a:FloatArray)=Matrix4d(DoubleArray(16){a[(it%4)*4+it/4].toDouble()})}
}
class FloorSessionTransform private constructor(private val f:Matrix4d){
 fun floorToSession(p:Vector3d)=f.inverseRigid().transform(p);fun sessionToFloor(p:Vector3d)=f.transform(p);fun floorObjectToSession(o:Matrix4d)=f.inverseRigid()*o
 fun cameraFloorPosition(c:Matrix4d):Point2D{val p=(f*c).transform(Vector3d(0.0,0.0,0.0));return Point2D(p.x,p.y)};fun matrix()=f
 companion object{fun atConfirmation(s:StartPose,c:Matrix4d,pitch:Double,roll:Double)=FloorSessionTransform(Matrix4d.rigid(Vector3d(s.x,s.y,1.5),Quaterniond.floorYawPitchRoll(s.yawRadians,pitch,roll))*c.inverseRigid())}
}
enum class CameraTracking{TRACKING,PAUSED,STOPPED}
data class TrackingSnapshot(val phase:NavigationPhase,val lastGoodPosition:Point2D?,val nonTrackingSinceMillis:Long?)
class TrackingStateMachine(initial:NavigationPhase=NavigationPhase.MAP_ONLY){var snapshot=TrackingSnapshot(initial,null,null);private set
 fun beginSettingPosition(){snapshot=snapshot.copy(phase=NavigationPhase.SETTING_POSITION,nonTrackingSinceMillis=null)}
 fun routeReady(){snapshot=snapshot.copy(phase=NavigationPhase.ROUTE_PREVIEW)};fun startAr(){snapshot=snapshot.copy(phase=NavigationPhase.NAVIGATING)}
 fun mapOnly(){snapshot=snapshot.copy(phase=NavigationPhase.MAP_ONLY,nonTrackingSinceMillis=null)}
 fun update(t:CameraTracking,now:Long,p:Point2D?,dest:Point2D){if(snapshot.phase!=NavigationPhase.NAVIGATING)return;if(t==CameraTracking.TRACKING&&p!=null){snapshot=TrackingSnapshot(if(p.distanceTo(dest)<=2)NavigationPhase.ARRIVED else NavigationPhase.NAVIGATING,p,null);return};val since=snapshot.nonTrackingSinceMillis?:now;snapshot=snapshot.copy(nonTrackingSinceMillis=since);if(t==CameraTracking.STOPPED||now-since>=1000)snapshot=snapshot.copy(phase=NavigationPhase.TRACKING_LOST)}
 fun recover(){snapshot=snapshot.copy(phase=NavigationPhase.SETTING_POSITION,nonTrackingSinceMillis=null)}
}
sealed interface ArCue{val position:Point2D;data class Turn(override val position:Point2D,val angle:Double):ArCue;data class Forward(override val position:Point2D):ArCue;data class Destination(override val position:Point2D):ArCue}
object CuePlanner{fun nextCue(route:List<Point2D>,visitor:Point2D,destination:Point2D):ArCue?{if(visitor.distanceTo(destination)<=15)return ArCue.Destination(destination);for(i in 1 until route.lastIndex){val a=atan2(route[i].y-route[i-1].y,route[i].x-route[i-1].x);val b=atan2(route[i+1].y-route[i].y,route[i+1].x-route[i].x);var d=b-a;while(d>PI)d-=2*PI;while(d< -PI)d+=2*PI;if(abs(d)>25*PI/180)return ArCue.Turn(route[i],d)};val n=route.drop(1).firstOrNull{visitor.distanceTo(it)>.5}?:return null;return if(visitor.distanceTo(n)>8)ArCue.Forward(Point2D((visitor.x+n.x)/2,(visitor.y+n.y)/2))else null}}
