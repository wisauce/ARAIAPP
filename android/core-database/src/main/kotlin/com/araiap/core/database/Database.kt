package com.araiap.core.database
import androidx.room.*
import com.araiap.core.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
@Entity(tableName="venues")data class VenueEntity(@PrimaryKey val id:String,val name:String,val publishedVersion:Int?)
@Entity(tableName="map_packages",primaryKeys=["venueId","version"])data class MapPackageEntity(val venueId:String,val version:Int,val floorId:String,val widthMeters:Double,val heightMeters:Double,val imageUrl:String,val imagePath:String,val downloadedAt:Long)
@Entity(tableName="destinations",primaryKeys=["venueId","version","id"])data class DestinationEntity(val venueId:String,val version:Int,val id:String,val name:String,val x:Double,val y:Double,val nodeId:String)
@Entity(tableName="route_nodes",primaryKeys=["venueId","version","id"])data class NodeEntity(val venueId:String,val version:Int,val id:String,val x:Double,val y:Double,val type:NodeType)
@Entity(tableName="route_edges",primaryKeys=["venueId","version","id"])data class EdgeEntity(val venueId:String,val version:Int,val id:String,val fromNodeId:String,val toNodeId:String,val distanceMeters:Double,val accessible:Boolean,val temporarilyClosed:Boolean)
@Entity(tableName="walkable_areas",primaryKeys=["venueId","version","id"])data class WalkableEntity(val venueId:String,val version:Int,val id:String,val points:String)
@Entity(tableName="obstacles",primaryKeys=["venueId","version","id"])data class ObstacleEntity(val venueId:String,val version:Int,val id:String,val points:String)
@Dao abstract class PublishedMapDao{
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun insertVenue(v:VenueEntity)
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun packages(v:MapPackageEntity)
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun destinations(v:List<DestinationEntity>)
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun nodes(v:List<NodeEntity>)
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun edges(v:List<EdgeEntity>)
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun walkable(v:List<WalkableEntity>)
 @Insert(onConflict=OnConflictStrategy.REPLACE)abstract suspend fun obstacles(v:List<ObstacleEntity>)
 @Query("SELECT * FROM map_packages WHERE venueId=:id ORDER BY version DESC LIMIT 1")abstract suspend fun latest(id:String):MapPackageEntity?
 @Query("SELECT * FROM destinations WHERE venueId=:id AND version=:v")abstract suspend fun getDest(id:String,v:Int):List<DestinationEntity>
 @Query("SELECT * FROM route_nodes WHERE venueId=:id AND version=:v")abstract suspend fun getNodes(id:String,v:Int):List<NodeEntity>
 @Query("SELECT * FROM route_edges WHERE venueId=:id AND version=:v")abstract suspend fun getEdges(id:String,v:Int):List<EdgeEntity>
 @Query("SELECT * FROM walkable_areas WHERE venueId=:id AND version=:v")abstract suspend fun getWalk(id:String,v:Int):List<WalkableEntity>
 @Query("SELECT * FROM obstacles WHERE venueId=:id AND version=:v")abstract suspend fun getObs(id:String,v:Int):List<ObstacleEntity>
 @Query("DELETE FROM map_packages WHERE venueId=:id")abstract suspend fun clearP(id:String)
 @Query("DELETE FROM destinations WHERE venueId=:id")abstract suspend fun clearD(id:String)
 @Query("DELETE FROM route_nodes WHERE venueId=:id")abstract suspend fun clearN(id:String)
 @Query("DELETE FROM route_edges WHERE venueId=:id")abstract suspend fun clearE(id:String)
 @Query("DELETE FROM walkable_areas WHERE venueId=:id")abstract suspend fun clearW(id:String)
 @Query("DELETE FROM obstacles WHERE venueId=:id")abstract suspend fun clearO(id:String)
 @Transaction open suspend fun replace(m:FloorMap,path:String,at:Long){require(m.status==MapStatus.PUBLISHED);clearP(m.venueId);clearD(m.venueId);clearN(m.venueId);clearE(m.venueId);clearW(m.venueId);clearO(m.venueId);packages(MapPackageEntity(m.venueId,m.version,m.id,m.widthMeters,m.heightMeters,m.imageUrl,path,at));destinations(m.destinations.map{DestinationEntity(m.venueId,m.version,it.id,it.name,it.x,it.y,it.nodeId)});nodes(m.routeNodes.map{NodeEntity(m.venueId,m.version,it.id,it.x,it.y,it.type)});edges(m.routeEdges.map{EdgeEntity(m.venueId,m.version,it.id,it.fromNodeId,it.toNodeId,it.distanceMeters,it.accessible,it.temporarilyClosed)});walkable(m.walkableAreas.map{WalkableEntity(m.venueId,m.version,it.id,Json.encodeToString(it.points))});obstacles(m.obstacles.map{ObstacleEntity(m.venueId,m.version,it.id,Json.encodeToString(it.points))})}
 @Transaction open suspend fun load(id:String):CachedMap?{val p=latest(id)?:return null;fun pts(s:String)=Json.decodeFromString<List<Point2D>>(s);return CachedMap(FloorMap(p.floorId,id,p.version,MapStatus.PUBLISHED,p.widthMeters,p.heightMeters,p.imageUrl,getWalk(id,p.version).map{Polygon2D(it.id,pts(it.points))},getObs(id,p.version).map{Polygon2D(it.id,pts(it.points))},getDest(id,p.version).map{Destination(it.id,it.name,it.x,it.y,it.nodeId)},getNodes(id,p.version).map{RouteNode(it.id,it.x,it.y,it.type)},getEdges(id,p.version).map{RouteEdge(it.id,it.fromNodeId,it.toNodeId,it.distanceMeters,it.accessible,it.temporarilyClosed)}),p.imagePath,p.downloadedAt)}
}
data class CachedMap(val map:FloorMap,val imagePath:String,val downloadedAt:Long)
@Database(entities=[VenueEntity::class,MapPackageEntity::class,DestinationEntity::class,NodeEntity::class,EdgeEntity::class,WalkableEntity::class,ObstacleEntity::class],version=1,exportSchema=false)abstract class AraiapDatabase:RoomDatabase(){abstract fun dao():PublishedMapDao}
fun Venue.toEntity()=VenueEntity(id,name,publishedVersion)
