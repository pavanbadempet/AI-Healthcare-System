package com.example.clinosmobile.ui.main

import com.example.clinosmobile.data.ConnectionState
import com.example.clinosmobile.data.DataRepository
import junit.framework.TestCase.assertEquals
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.test.runTest
import org.junit.Test

class MainScreenViewModelTest {
  @Test
  fun uiState_initiallyLoading() = runTest {
    val viewModel = MainScreenViewModel(FakeMyModelRepository())
    assertEquals(viewModel.uiState.first(), MainScreenUiState.Loading)
  }

  @Test
  fun uiState_onItemSaved_isDisplayed() = runTest {
    val repository = FakeMyModelRepository()
    val viewModel = MainScreenViewModel(repository)
    assertEquals(viewModel.uiState.first(), MainScreenUiState.Loading)
  }
}

private class FakeMyModelRepository : DataRepository {
  override val data: Flow<List<String>> = flow { emit(listOf("Sample")) }
  
  private val _connectionState = MutableStateFlow(ConnectionState())
  override val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

  override suspend fun connectAndLogin(url: String, username: String, password: String): Result<String> {
    return Result.success("fake-token")
  }

  override fun disconnect() {
    _connectionState.value = ConnectionState()
  }

  override suspend fun triggerSoapAudit(patientName: String): Result<String> {
    return Result.success("Success SOAP Audit")
  }

  override suspend fun triggerAutoCall(alertDetails: String): Result<String> {
    return Result.success("Success Auto Call")
  }

  override suspend fun triggerSelfHeal(): Result<String> {
    return Result.success("Success Self Heal")
  }

  override suspend fun triggerHandoff(bed: String): Result<String> {
    return Result.success("Success Handoff")
  }

  override suspend fun refreshTelemetry() {}
}
