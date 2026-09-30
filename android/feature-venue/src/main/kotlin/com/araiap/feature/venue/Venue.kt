package com.araiap.feature.venue
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.*
import com.araiap.core.model.Venue
import com.araiap.core.network.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject
class VenueRepository @Inject constructor(private val api:AraiapApi){suspend fun list()=apiCall{api.venues()};suspend fun create(n:String)=apiCall{api.createVenue(CreateVenueRequest(n))}}
data class VenueScreenState(val venues:List<Venue> = emptyList(),val name:String="",val loading:Boolean=false,val error:String?=null)
sealed interface VenueAction{data object Refresh:VenueAction;data class Name(val v:String):VenueAction;data object Create:VenueAction}
@HiltViewModel class VenueViewModel @Inject constructor(private val repo:VenueRepository):ViewModel(){var state by mutableStateOf(VenueScreenState());private set
 fun dispatch(a:VenueAction){when(a){is VenueAction.Name->state=state.copy(name=a.v);VenueAction.Refresh->viewModelScope.launch{state=state.copy(loading=true);when(val r=repo.list()){is NetworkResult.Success->state=state.copy(venues=r.value,loading=false);is NetworkResult.Failure->state=state.copy(error=r.message,loading=false)}};VenueAction.Create->viewModelScope.launch{when(val r=repo.create(state.name)){is NetworkResult.Success->state=state.copy(venues=state.venues+r.value,name="");is NetworkResult.Failure->state=state.copy(error=r.message)}}}}}
@Composable fun VenueListScreen(managerMode:Boolean,onVenueSelected:(Venue)->Unit,vm:VenueViewModel=hiltViewModel()){LaunchedEffect(Unit){vm.dispatch(VenueAction.Refresh)};val s=vm.state;val shown=if(managerMode)s.venues else s.venues.filter{it.publishedVersion!=null};Column(Modifier.fillMaxSize().padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Text(if(managerMode)"Manage venues" else "Choose a venue",style=MaterialTheme.typography.headlineMedium);if(managerMode)Row{OutlinedTextField(s.name,{vm.dispatch(VenueAction.Name(it))},Modifier.weight(1f),label={Text("Venue name")});Button({vm.dispatch(VenueAction.Create)}){Text("Create")}};s.error?.let{Text(it,color=MaterialTheme.colorScheme.error)};LazyColumn{items(shown,key={it.id}){v->Card(Modifier.fillMaxWidth().padding(4.dp).clickable{onVenueSelected(v)}){Column(Modifier.padding(16.dp)){Text(v.name);Text("Published version ${v.publishedVersion?:"none"}")}}}}}}
