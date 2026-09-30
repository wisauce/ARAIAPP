package com.araiap.core.ar
import com.araiap.core.model.*;import org.junit.Assert.*;import org.junit.Test;import kotlin.math.PI
class ArTest{@Test fun yaw(){val p=Matrix4d.rigid(Vector3d(0.0,0.0,0.0),Quaterniond.floorYawPitchRoll(PI/2,0.0,0.0)).transform(Vector3d(1.0,0.0,0.0));assertEquals(0.0,p.x,1e-8);assertEquals(1.0,p.y,1e-8)}
@Test fun roundTrip(){val c=Matrix4d.rigid(Vector3d(4.0,2.0,-1.0),Quaterniond.floorYawPitchRoll(.2,.1,0.0));val t=FloorSessionTransform.atConfirmation(StartPose(8.0,9.0,.3),c,.1,0.0);val p=Vector3d(3.0,4.0,.05);val r=t.sessionToFloor(t.floorToSession(p));assertEquals(p.x,r.x,1e-8);assertEquals(p.y,r.y,1e-8)}
private fun machine()=TrackingStateMachine().apply{beginSettingPosition();routeReady();startAr()}
@Test fun lossTimer(){val m=machine();m.update(CameraTracking.PAUSED,0,null,Point2D(9.0,0.0));m.update(CameraTracking.PAUSED,999,null,Point2D(9.0,0.0));assertEquals(NavigationPhase.NAVIGATING,m.snapshot.phase);m.update(CameraTracking.PAUSED,1000,null,Point2D(9.0,0.0));assertEquals(NavigationPhase.TRACKING_LOST,m.snapshot.phase)}
@Test fun arrival(){val m=machine();m.update(CameraTracking.TRACKING,0,Point2D(8.0,0.0),Point2D(10.0,0.0));assertEquals(NavigationPhase.ARRIVED,m.snapshot.phase)}
@Test fun cue(){assertTrue(CuePlanner.nextCue(listOf(Point2D(0.0,0.0),Point2D(10.0,0.0),Point2D(10.0,10.0)),Point2D(0.0,0.0),Point2D(30.0,30.0)) is ArCue.Turn)}
}
