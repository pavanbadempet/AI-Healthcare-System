package com.example.clinosmobile.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.clinosmobile.data.ConnectionState
import com.example.clinosmobile.data.DataRepository
import com.example.clinosmobile.ui.main.MainScreenUiState.Success
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class MainScreenViewModel(private val dataRepository: DataRepository) : ViewModel() {
  val uiState: StateFlow<MainScreenUiState> =
    dataRepository.data
      .map<List<String>, MainScreenUiState>(::Success)
      .catch { emit(MainScreenUiState.Error(it)) }
      .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), MainScreenUiState.Loading)

  val connectionState: StateFlow<ConnectionState> = dataRepository.connectionState

  fun connect(url: String, username: String, password: String, onResult: (Result<String>) -> Unit) {
    viewModelScope.launch {
      val result = dataRepository.connectAndLogin(url, username, password)
      onResult(result)
    }
  }

  fun disconnect() {
    dataRepository.disconnect()
  }

  fun triggerSoapAudit(patientName: String, onResult: (Result<String>) -> Unit) {
    viewModelScope.launch {
      val result = dataRepository.triggerSoapAudit(patientName)
      onResult(result)
    }
  }

  fun triggerAutoCall(alertDetails: String, onResult: (Result<String>) -> Unit) {
    viewModelScope.launch {
      val result = dataRepository.triggerAutoCall(alertDetails)
      onResult(result)
    }
  }

  fun triggerSelfHeal(onResult: (Result<String>) -> Unit) {
    viewModelScope.launch {
      val result = dataRepository.triggerSelfHeal()
      onResult(result)
    }
  }

  fun triggerHandoff(bed: String, onResult: (Result<String>) -> Unit) {
    viewModelScope.launch {
      val result = dataRepository.triggerHandoff(bed)
      onResult(result)
    }
  }

  fun refresh() {
    viewModelScope.launch {
      dataRepository.refreshTelemetry()
    }
  }
}

sealed interface MainScreenUiState {
  object Loading : MainScreenUiState

  data class Error(val throwable: Throwable) : MainScreenUiState

  data class Success(val data: List<String>) : MainScreenUiState
}
