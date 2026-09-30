package com.araiap.app
import android.app.Application
import android.content.Context
import android.os.Bundle
import androidx.activity.*
import androidx.activity.compose.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.room.Room
import com.araiap.core.database.*
import com.araiap.core.network.*
import com.araiap.feature.floor.editor.FloorEditorScreen
import com.araiap.feature.navigation.VisitorNavigationScreen
import com.araiap.feature.venue.VenueListScreen
import dagger.*
import dagger.hilt.*
import dagger.hilt.android.*
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton
@HiltAndroidApp class AraiapApplication:Application()
@Module @InstallIn(SingletonComponent::class)object DataModule{@Provides @Singleton fun api()=ApiFactory.create(BuildConfig.API_BASE_URL);@Provides @Singleton fun db(@ApplicationContext c:Context)=Room.databaseBuilder(c,AraiapDatabase::class.java,"araiap.db").build();@Provides fun dao(d:AraiapDatabase)=d.dao()}
@AndroidEntryPoint class MainActivity:ComponentActivity(){override fun onCreate(b:Bundle?){super.onCreate(b);setContent{MaterialTheme{Surface(Modifier.fillMaxSize()){Root()}}}}}
private enum class Screen{ROLE,MANAGER,EDITOR,VISITOR,NAV}
@Composable private fun Root(){var screen by rememberSaveable{mutableStateOf(Screen.ROLE)};var venue by rememberSaveable{mutableStateOf<String?>(null)};BackHandler(screen!=Screen.ROLE){screen=when(screen){Screen.EDITOR->Screen.MANAGER;Screen.NAV->Screen.VISITOR;else->Screen.ROLE}};when(screen){Screen.ROLE->Column(Modifier.fillMaxSize().padding(24.dp),verticalArrangement=Arrangement.spacedBy(16.dp)){Text("Araiap",style=MaterialTheme.typography.displaySmall);Text("Indoor navigation with an always-available 2D route.");Button({screen=Screen.VISITOR}){Text("Visit a venue")};Button({screen=Screen.MANAGER}){Text("Manage a venue")}};Screen.MANAGER->VenueListScreen(true){venue=it.id;screen=Screen.EDITOR};Screen.EDITOR->venue?.let{FloorEditorScreen(it)};Screen.VISITOR->VenueListScreen(false){venue=it.id;screen=Screen.NAV};Screen.NAV->venue?.let{VisitorNavigationScreen(it)}}}
