package com.araiap.core.model
import org.junit.Assert.*;import org.junit.Test
class ModelTest{@Test fun calibration(){val c=Calibration(4000,2500,500.0,10.0);assertEquals(80.0,c.widthMeters,1e-6);assertEquals(50.0,c.heightMeters,1e-6)}@Test(expected=IllegalArgumentException::class)fun badCalibration(){Calibration(1,1,0.0,1.0)}@Test fun distance(){assertEquals(5.0,Point2D(0.0,0.0).distanceTo(Point2D(3.0,4.0)),1e-6)}}
