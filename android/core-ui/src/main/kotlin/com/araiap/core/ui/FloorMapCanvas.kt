package com.araiap.core.ui
import android.graphics.BitmapFactory
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import com.araiap.core.model.*
import kotlin.math.*
@Composable fun FloorMapCanvas(map:FloorMap,route:List<Point2D>,pose:StartPose?,modifier:Modifier=Modifier,imagePath:String?=null,onMapTap:(Point2D)->Unit={}){
 val bitmap=remember(imagePath){imagePath?.let(BitmapFactory::decodeFile)?.asImageBitmap()}
 Box(modifier){bitmap?.let{Image(it,"Floor plan",Modifier.fillMaxSize(),contentScale=ContentScale.Fit)}
 Canvas(Modifier.fillMaxSize().pointerInput(map.id,map.version){detectTapGestures{p->val s=min(size.width/map.widthMeters,size.height/map.heightMeters);val l=(size.width-map.widthMeters*s)/2;val t=(size.height-map.heightMeters*s)/2;onMapTap(Point2D((p.x-l)/s,map.heightMeters-(p.y-t)/s))}}){val s=min(size.width/map.widthMeters,size.height/map.heightMeters);val l=(size.width-map.widthMeters*s)/2;val t=(size.height-map.heightMeters*s)/2;fun at(p:Point2D)=Offset((l+p.x*s).toFloat(),(t+(map.heightMeters-p.y)*s).toFloat());fun path(p:Polygon2D)=Path().apply{p.points.firstOrNull()?.let{moveTo(at(it).x,at(it).y);p.points.drop(1).forEach{q->lineTo(at(q).x,at(q).y)};close()}}
 if(bitmap==null)drawRect(Color(0xfff5f5f2));map.walkableAreas.forEach{drawPath(path(it),Color(0x44a0c0a0));drawPath(path(it),Color.DarkGray,style=Stroke(2f))};map.obstacles.forEach{drawPath(path(it),Color.Gray)}
 if(route.size>1){val p=Path().apply{moveTo(at(route[0]).x,at(route[0]).y);route.drop(1).forEach{q->lineTo(at(q).x,at(q).y)}};drawPath(p,Color.Blue,style=Stroke(8f))}
 map.destinations.forEach{drawCircle(Color(0xff006c4c),7f,at(it.point))};pose?.let{drawCircle(Color.Blue,10f,at(it.point));drawLine(Color.Blue,at(it.point),Offset(at(it.point).x+cos(it.yawRadians).toFloat()*35,at(it.point).y-sin(it.yawRadians).toFloat()*35),7f)}
 }}}
