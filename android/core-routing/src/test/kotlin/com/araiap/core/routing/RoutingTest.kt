package com.araiap.core.routing
import com.araiap.core.model.*;import org.junit.Assert.*;import org.junit.Test
class RoutingTest{val area=Polygon2D("a",listOf(Point2D(0.0,0.0),Point2D(20.0,0.0),Point2D(20.0,20.0),Point2D(0.0,20.0)));val a=RouteNode("a",1.0,1.0,NodeType.ENDPOINT);val b=RouteNode("b",5.0,1.0,NodeType.INTERSECTION);val c=RouteNode("c",5.0,6.0,NodeType.INTERSECTION);val d=RouteNode("d",9.0,1.0,NodeType.DOOR)
 fun edge(id:String,x:RouteNode,y:RouteNode,access:Boolean=true,closed:Boolean=false)=RouteEdge(id,x.id,y.id,x.point.distanceTo(y.point),access,closed)
 fun map(edges:List<RouteEdge>,obs:List<Polygon2D> = emptyList())=FloorMap("f","v",1,MapStatus.PUBLISHED,20.0,20.0,"x",listOf(area),obs,listOf(Destination("dest","D",9.0,1.0,"d")),listOf(a,b,c,d),edges)
 @Test fun shortest(){assertEquals(listOf("a","b","d"),(findRoute(map(listOf(edge("ab",a,b),edge("bd",b,d),edge("ac",a,c),edge("cd",c,d))),a.point,"dest",false)as RouteResult.Found).nodeIds)}
 @Test fun closed(){assertEquals(listOf("a","c","d"),(findRoute(map(listOf(edge("ab",a,b,closed=true),edge("bd",b,d),edge("ac",a,c),edge("cd",c,d))),a.point,"dest",false)as RouteResult.Found).nodeIds)}
 @Test fun accessible(){assertEquals(listOf("a","c","d"),(findRoute(map(listOf(edge("ab",a,b,false),edge("bd",b,d),edge("ac",a,c),edge("cd",c,d))),a.point,"dest",true)as RouteResult.Found).nodeIds)}
 @Test fun bowTie(){assertFalse(isSimplePolygon(Polygon2D("x",listOf(Point2D(0.0,0.0),Point2D(2.0,2.0),Point2D(0.0,2.0),Point2D(2.0,0.0)))))}
 @Test fun outside(){assertFalse(isWalkable(map(emptyList()),Point2D(30.0,1.0)))}
 @Test fun normalizes(){assertEquals(4.0,normalizedEdges(map(listOf(edge("x",a,b).copy(distanceMeters=99.0)))).single().distanceMeters,1e-6)}
}
