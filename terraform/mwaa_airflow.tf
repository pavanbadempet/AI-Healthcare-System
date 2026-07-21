# AWS MWAA (Managed Workflows for Apache Airflow) Terraform Infrastructure Manifest

resource "aws_mwaa_environment" "healthcare_mwaa" {
  name               = "healthcare-airflow-prod"
  airflow_version    = "2.8.1"
  environment_class  = "mw1.medium"
  execution_role_arn = aws_iam_role.mwaa_execution_role.arn

  source_bucket_arn = aws_s3_bucket.airflow_dags_bucket.arn
  dag_s3_path       = "airflow/dags"

  network_configuration {
    security_group_ids = [aws_security_group.mwaa_sg.id]
    subnet_ids         = var.private_subnet_ids
  }

  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = "INFO"
    }
    scheduler_logs {
      enabled   = true
      log_level = "INFO"
    }
  }
}
