package com.araiap.core.model
import kotlinx.serialization.Serializable
import kotlin.math.hypot
@Serializable data class Venue(val id:String,val name:String,val publishedVersion:Int?=null,val floorId:String?=null)
@Serializable data class FloorMap(val id:String,val venueId:String,val version:Int,val status:MapStatus,val widthMeters:Double=0.0,val heightMeters:Double=0.0,val imageUrl:String,val walkableAreas:List<Polygon2D> = emptyList(),val obstacles:List<Polygon2D> = emptyList(),val destinations:List<Destination> = emptyList(),val routeNodes:List<RouteNode> = emptyList(),val routeEdges:List<RouteEdge> = emptyList())
@Serializable enum class MapStatus{DRAFT,PUBLISHED,ARCHIVED}
@Serializable data class Polygon2D(val id:String,val points:List<Point2D>)
@Serializable data class Point2D(val x:Double,val y:Double){fun distanceTo(o:Point2D)=hypot(x-o.x,y-o.y)}
@Serializable data class Destination(val id:String,val name:String,val x:Double,val y:Double,val nodeId:String){val point get()=Point2D(x,y)}
@Serializable data class RouteNode(val id:String,val x:Double,val y:Double,val type:NodeType){val point get()=Point2D(x,y)}
@Serializable enum class NodeType{INTERSECTION,DOOR,ENDPOINT}
@Serializable data class RouteEdge(val id:String,val fromNodeId:String,val toNodeId:String,val distanceMeters:Double,val accessible:Boolean,val temporarilyClosed:Boolean)
@Serializable data class StartPose(val x:Double,val y:Double,val yawRadians:Double){val point get()=Point2D(x,y)}
sealed interface RouteResult{data class Found(val nodeIds:List<String>,val distanceMeters:Double):RouteResult;data object StartOffGraph:RouteResult;data object DestinationMissing:RouteResult;data object Unreachable:RouteResult}
enum class NavigationPhase{MAP_ONLY,SETTING_POSITION,ROUTE_PREVIEW,NAVIGATING,TRACKING_LOST,ARRIVED}
data class Calibration(val pixelWidth:Int,val pixelHeight:Int,val lineLengthPixels:Double,val realLengthMeters:Double){
 init{require(pixelWidth>0&&pixelHeight>0&&lineLengthPixels>0&&realLengthMeters>0)}
 val metersPerPixel get()=realLengthMeters/lineLengthPixels
 val widthMeters get()=pixelWidth*metersPerPixel
 val heightMeters get()=pixelHeight*metersPerPixel
}
