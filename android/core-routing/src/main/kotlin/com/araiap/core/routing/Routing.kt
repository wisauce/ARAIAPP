package com.araiap.core.routing
import com.araiap.core.model.*
import java.util.PriorityQueue
import kotlin.math.abs
private const val E=1e-9
private fun cross(a:Point2D,b:Point2D,c:Point2D)=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)
private fun on(p:Point2D,a:Point2D,b:Point2D)=abs(cross(a,b,p))<=E&&p.x>=minOf(a.x,b.x)-E&&p.x<=maxOf(a.x,b.x)+E&&p.y>=minOf(a.y,b.y)-E&&p.y<=maxOf(a.y,b.y)+E
private fun intersects(a:Point2D,b:Point2D,c:Point2D,d:Point2D):Boolean{
 val o1=cross(a,b,c);val o2=cross(a,b,d);val o3=cross(c,d,a);val o4=cross(c,d,b)
 return ((o1>E&&o2< -E)||(o1< -E&&o2>E))&&((o3>E&&o4< -E)||(o3< -E&&o4>E))||abs(o1)<=E&&on(c,a,b)||abs(o2)<=E&&on(d,a,b)||abs(o3)<=E&&on(a,c,d)||abs(o4)<=E&&on(b,c,d)
}
fun pointInPolygon(p:Point2D,poly:Polygon2D):Boolean{if(poly.points.size<3)return false;var inside=false;for(i in poly.points.indices){val a=poly.points[i];val b=poly.points[(i+1)%poly.points.size];if(on(p,a,b))return true;if((a.y>p.y)!=(b.y>p.y)&&p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x)inside=!inside};return inside}
fun isWalkable(m:FloorMap,p:Point2D)=m.walkableAreas.any{pointInPolygon(p,it)}&&m.obstacles.none{pointInPolygon(p,it)}
fun isSimplePolygon(p:Polygon2D):Boolean{if(p.points.size<3)return false;for(i in p.points.indices){val a=p.points[i];val b=p.points[(i+1)%p.points.size];if(a.distanceTo(b)<=E)return false;for(j in i+1 until p.points.size){if(j==i||j==(i+1)%p.points.size||(j+1)%p.points.size==i)continue;if(intersects(a,b,p.points[j],p.points[(j+1)%p.points.size]))return false}};return abs(p.points.indices.sumOf{val a=p.points[it];val b=p.points[(it+1)%p.points.size];a.x*b.y-b.x*a.y})>E}
fun segmentIsNavigable(m:FloorMap,a:Point2D,b:Point2D):Boolean{if(!isWalkable(m,a)||!isWalkable(m,b))return false;for(p in m.obstacles)for(i in p.points.indices)if(intersects(a,b,p.points[i],p.points[(i+1)%p.points.size]))return false;val samples=64;return(0..samples).all{val t=it.toDouble()/samples;isWalkable(m,Point2D(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t))}}
fun findRoute(map:FloorMap,start:Point2D,destinationId:String,requireAccessible:Boolean):RouteResult{
 if(map.status!=MapStatus.PUBLISHED)return RouteResult.Unreachable
 val dest=map.destinations.firstOrNull{it.id==destinationId}?:return RouteResult.DestinationMissing
 val nodes=map.routeNodes.associateBy{it.id};val goal=nodes[dest.nodeId]?:return RouteResult.DestinationMissing
 val area=map.walkableAreas.firstOrNull{pointInPolygon(start,it)}?:return RouteResult.StartOffGraph
 if(map.obstacles.any{pointInPolygon(start,it)})return RouteResult.StartOffGraph
 val first=map.routeNodes.filter{pointInPolygon(it.point,area)&&segmentIsNavigable(map,start,it.point)}.minByOrNull{start.distanceTo(it.point)}?:return RouteResult.StartOffGraph
 data class Q(val id:String,val f:Double);val q=PriorityQueue(compareBy<Q>{it.f});val g=mutableMapOf(first.id to start.distanceTo(first.point));val prev=mutableMapOf<String,String>()
 q+=Q(first.id,g.getValue(first.id)+first.point.distanceTo(goal.point))
 val edges=map.routeEdges.filter{!it.temporarilyClosed&&(!requireAccessible||it.accessible)&&nodes[it.fromNodeId]!=null&&nodes[it.toNodeId]!=null&&segmentIsNavigable(map,nodes.getValue(it.fromNodeId).point,nodes.getValue(it.toNodeId).point)}.groupBy{it.fromNodeId}
 while(q.isNotEmpty()){val c=q.remove();val cg=g[c.id]?:continue;if(c.id==goal.id){val path=generateSequence(goal.id){prev[it]}.toList().asReversed();return RouteResult.Found(path,cg)};for(e in edges[c.id].orEmpty()){val n=nodes.getValue(e.toNodeId);val ng=cg+nodes.getValue(c.id).point.distanceTo(n.point);if(ng+E<(g[n.id]?:Double.POSITIVE_INFINITY)){g[n.id]=ng;prev[n.id]=c.id;q+=Q(n.id,ng+n.point.distanceTo(goal.point))}}}
 return RouteResult.Unreachable
}
data class ValidationIssue(val field:String,val message:String)
object PublishValidator{fun validate(m:FloorMap)=buildList{
 if(m.widthMeters<=0||m.heightMeters<=0)add(ValidationIssue("calibration","Scale has not been calibrated."))
 if(m.walkableAreas.isEmpty())add(ValidationIssue("walkableAreas","At least one walkable polygon is required."))
 (m.walkableAreas+m.obstacles).filterNot(::isSimplePolygon).forEach{add(ValidationIssue("polygon:${it.id}","Polygon self-intersects."))}
 if(m.destinations.isEmpty())add(ValidationIssue("destinations","At least one destination is required."))
 val nodes=m.routeNodes.associateBy{it.id};val seen=mutableSetOf<Pair<String,String>>()
 m.routeEdges.forEach{if(it.fromNodeId !in nodes||it.toNodeId !in nodes)add(ValidationIssue("edge:${it.id}","Missing node."));if(!seen.add(it.fromNodeId to it.toNodeId))add(ValidationIssue("edge:${it.id}","Duplicate directed edge."))}
 m.destinations.forEach{d->val n=nodes[d.nodeId];when{!isWalkable(m,d.point)->add(ValidationIssue("destination:${d.id}","Destination outside walkable space."));n==null->add(ValidationIssue("destination:${d.id}","Missing destination node."));n.type!=NodeType.DOOR->add(ValidationIssue("destination:${d.id}","Destination must use a door node."));d.point.distanceTo(n.point)>1.0+E->add(ValidationIssue("destination:${d.id}","Destination node is farther than 1 metre."));m.routeEdges.none{it.toNodeId==d.nodeId}->add(ValidationIssue("destination:${d.id}","Destination has no incoming route."))}}
}}
fun normalizedEdges(m:FloorMap):List<RouteEdge>{val n=m.routeNodes.associateBy{it.id};return m.routeEdges.map{e->val a=n[e.fromNodeId];val b=n[e.toNodeId];if(a==null||b==null)e else e.copy(distanceMeters=a.point.distanceTo(b.point))}}
