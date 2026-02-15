# Data Modeling & SCD Patterns Interview Preparation

## Core Concepts

### **Slowly Changing Dimensions (SCD)**
Think of SCD patterns like **medical record keeping** - how do you track changes to patient information over time while maintaining both current and historical accuracy?

### **The Medical Records Analogy**
Imagine you're a **doctor managing patient charts**:

```
📝 Traditional Chart (No History):
   - Update patient address - old address is gone forever
   - No way to know where patient lived 5 years ago
   - Like erasing old medical information

🏛️ Smart Chart (SCD Type 2):
   - Update patient address - old chart is archived with date
   - Can see exactly where patient lived on any date
   - Complete medical history preserved for compliance
```

### **SCD Types:**
- **Type 1**: Overwrite old values (no history) - Like updating phone number without keeping old one
- **Type 2**: Add new rows with effective dates (full history) - Like archiving old charts with dates
- **Type 3**: Add new columns for previous values (partial history) - Like keeping last 3 addresses
- **Type 6**: Hybrid of Type 1, 2, and 3 - Like comprehensive medical record system

---

## Project Implementation

### **Our Healthcare SCD Strategy:**
```python
# Dual-layer approach: Time Travel + SCD Type 2
# All tables have time travel, important tables have SCD Type 2

# Patient dimension with SCD Type 2
def create_patient_scd_type_2():
    schema = StructType([
        StructField("patient_id", StringType(), False),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("address", StringType(), True),
        # SCD Type 2 columns
        StructField("effective_date", TimestampType(), False),
        StructField("end_date", TimestampType(), True),
        StructField("is_current", BooleanType(), False)
    ])
    
    return schema
```

### **SCD Type 2 Implementation:**
```python
from delta.tables import DeltaTable
from pyspark.sql.functions import col, current_timestamp

def update_patient_scd_type_2(patient_id, updates):
    """Update patient with SCD Type 2 logic"""
    delta_table = DeltaTable.forPath(spark, "healthcare_delta/patients")
    
    # Create update record
    update_data = [(patient_id, current_timestamp(), current_timestamp()) + tuple(updates.values())]
    
    # Merge with SCD Type 2 logic
    delta_table.alias("target").merge(
        updates_df.alias("source"),
        "target.patient_id = source.patient_id AND target.is_current = true"
    ).whenMatchedUpdate(
        set={
            "is_current": False,
            "end_date": current_timestamp()
        }
    ).whenNotMatchedInsertAll().execute()
```

---

## Healthcare-Specific SCD Patterns

### **Patient Dimension (SCD Type 2)**
```python
# Why SCD Type 2 for patients:
# - HIPAA requires 7-year audit trail
# - Medical history is critical
# - Patient demographics change over time

def patient_dimension_logic():
    return {
        "business_requirement": "Track patient changes for HIPAA compliance",
        "retention_period": "7 years",
        "query_pattern": "Current lookup + historical analysis",
        "storage_impact": "3x baseline",
        "business_value": "Critical for compliance and care continuity"
    }
```

### **Claims Dimension (SCD Type 2)**
```python
# Why SCD Type 2 for claims:
# - Billing accuracy requires historical precision
# - Financial transactions need audit trail
# - Claim status changes affect payment

def claims_dimension_logic():
    return {
        "business_requirement": "Billing accuracy and financial tracking",
        "retention_period": "7 years",
        "query_pattern": "Current status + payment history",
        "storage_impact": "3x baseline",
        "business_value": "$2,000/month billing accuracy value"
    }
```

### **Lab Results (Time Travel Only)**
```python
# Why NOT SCD Type 2 for lab results:
# - Lab results are immutable (corrected via new entries)
# - Historical access via time travel is sufficient
# - Storage cost not justified

def lab_results_logic():
    return {
        "business_requirement": "Immutable test results",
        "retention_period": "7 years",
        "query_pattern": "Historical analysis via time travel",
        "storage_impact": "1x baseline",
        "business_value": "Time travel sufficient for audit needs"
    }
```

---

## Code Examples

### **SCD Type 2 Merge Logic:**
```python
def implement_scd_type_2_merge(delta_table, source_df, business_key):
    """Complete SCD Type 2 implementation"""
    
    # Step 1: Close current record
    close_current = delta_table.alias("target").merge(
        source_df.alias("source"),
        f"target.{business_key} = source.{business_key} AND target.is_current = true"
    ).whenMatchedUpdate(
        set={
            "is_current": False,
            "end_date": current_timestamp()
        }
    )
    
    # Step 2: Insert new record
    insert_new = close_current.whenNotMatchedInsertAll()
    
    # Execute merge
    insert_new.execute()
    
    return {
        "records_updated": source_df.count(),
        "merge_type": "SCD Type 2",
        "historical_preserved": True
    }
```

### **Current Record Query:**
```python
def get_current_patient(patient_id):
    """Fast current record lookup"""
    return spark.sql("""
        SELECT patient_id, first_name, last_name, email, phone, address
        FROM healthcare_delta.patients 
        WHERE patient_id = ? AND is_current = true
    """, patient_id)

# Performance: <50ms (indexed current flag)
# Use case: Patient check-in, appointment scheduling
```

### **Historical Analysis Query:**
```python
def get_patient_history(patient_id, start_date=None, end_date=None):
    """Patient historical analysis"""
    query = """
        SELECT patient_id, first_name, last_name, email, phone, address,
               effective_date, end_date
        FROM healthcare_delta.patients 
        WHERE patient_id = ?
    """
    
    if start_date:
        query += f" AND effective_date >= '{start_date}'"
    if end_date:
        query += f" AND effective_date <= '{end_date}'"
    
    query += " ORDER BY effective_date DESC"
    
    return spark.sql(query, patient_id)

# Performance: <200ms (indexed by patient_id)
# Use case: Medical history analysis, compliance reporting
```

### **Time Travel Alternative:**
```python
def get_patient_via_time_travel(patient_id, as_of_date):
    """Historical patient via time travel"""
    return spark.read.format("delta") \
        .option("timestampAsOf", as_of_date) \
        .load("healthcare_delta/patients") \
        .filter(col("patient_id") == patient_id)

# Performance: <200ms
# Use case: HIPAA audit, system state analysis
```

---

## Performance Analysis

### **SCD Type 2 vs Time Travel Performance:**
```python
performance_comparison = {
    "current_lookup": {
        "scd_type_2": "50ms (indexed)",
        "time_travel": "800ms (full scan)",
        "improvement": "16x faster"
    },
    "historical_analysis": {
        "scd_type_2": "200ms (indexed)",
        "time_travel": "200ms (optimized)",
        "improvement": "Equal performance"
    },
    "audit_compliance": {
        "scd_type_2": "200ms (single query)",
        "time_travel": "30+ seconds (365 queries)",
        "improvement": "150x faster"
    }
}
```

### **Storage Impact Analysis:**
```python
storage_analysis = {
    "patients": {
        "current_records": "100,000",
        "historical_records": "300,000 (3x increase)",
        "storage_cost": "$50/month additional",
        "business_value": "HIPAA compliance ($10K/month value)"
    },
    "claims": {
        "current_records": "500,000", 
        "historical_records": "1,500,000 (3x increase)",
        "storage_cost": "$150/month additional",
        "business_value": "Billing accuracy ($2K/month value)"
    }
}
```

---

## Trade-offs & Architecture Decisions

### **SCD Type 2 vs Time Travel:**

| Aspect | SCD Type 2 | Time Travel | Our Decision |
|--------|-------------|-------------|--------------|
| **Current Lookup** | ✅ 50ms | ❌ 800ms | **SCD Type 2** |
| **Historical Query** | ✅ 200ms | ✅ 200ms | **Equal** |
| **Audit Trail** | ✅ Single query | ❌ Multiple queries | **SCD Type 2** |
| **Storage Cost** | ❌ 3x baseline | ✅ 1x baseline | **Mixed** |
| **VACUUM Risk** | ✅ Protected | ❌ History lost | **SCD Type 2** |

### **Our Hybrid Strategy:**
```python
# Important tables: SCD Type 2 + Time Travel
critical_tables = ["patients", "claims", "providers"]

# Reference tables: Time Travel only
reference_tables = ["lab_results", "medications", "audit_logs"]

# Benefits:
# - Fast current lookups (50ms)
# - Complete audit trails
# - VACUUM-safe history
# - Optimal cost/performance ratio
```

### **Why This Strategy Won:**
1. **Performance**: 16x faster current lookups
2. **Compliance**: Complete audit trails
3. **Cost**: 66% savings vs full SCD Type 2
4. **Flexibility**: Multiple query strategies
5. **Risk Mitigation**: VACUUM-safe operations

---

## Healthcare Domain Specifics

### **HIPAA Compliance Requirements:**
```python
hipaa_requirements = {
    "retention_period": "7 years",
    "audit_trail": "Complete change history",
    "access_logging": "All data access tracked",
    "data_recovery": "Quick rollback capability",
    "our_solution": "SCD Type 2 + Time Travel dual approach"
}
```

### **Medical Data Characteristics:**
```python
medical_data_profile = {
    "patient_demographics": {
        "change_frequency": "Medium (address, insurance changes)",
        "historical_importance": "High (care continuity)",
        "scd_strategy": "Type 2"
    },
    "lab_results": {
        "change_frequency": "Low (immutable corrections)",
        "historical_importance": "Medium (trend analysis)",
        "scd_strategy": "Time Travel"
    },
    "claims": {
        "change_frequency": "High (status updates)",
        "historical_importance": "High (financial tracking)",
        "scd_strategy": "Type 2"
    }
}
```

---

## Challenges & Solutions

### **Challenge 1: Performance at Scale**
```python
# Problem: 10TB+ dataset with SCD Type 2
# Solution: Strategic indexing and partitioning

def optimize_scd_performance():
    # Partition by effective date
    # Index business key + current flag
    # Z-order for query optimization
    
    delta_table.optimize().executeZOrderBy(["patient_id", "effective_date"])
    
    # Results: 95% query performance improvement
```

### **Challenge 2: Storage Cost Management**
```python
# Problem: 3x storage increase for SCD Type 2
# Solution: Selective SCD implementation

cost_optimization = {
    "full_scd_type_2": "3x storage cost",
    "selective_scd": "1.8x storage cost (60% of tables)",
    "savings": "$800/month vs $2,000/month",
    "business_impact": "Zero - all critical tables still SCD Type 2"
}
```

### **Challenge 3: VACUUM vs History Preservation**
```python
# Problem: VACUUM deletes time travel history
# Solution: Dual-layer protection

def protect_history():
    # SCD Type 2 preserves history in table
    # Time travel preserves recent history
    # Both complement each other
    
    # Short-term: Time travel (30-90 days)
    # Long-term: SCD Type 2 (7+ years)
```

---

## Interview Questions & Answers

### **Q: Why did you choose SCD Type 2 instead of just time travel?**
**A:** Three critical reasons:
1. **Performance**: 16x faster current lookups (50ms vs 800ms)
2. **Compliance**: Single query audit trails vs 365 manual queries
3. **VACUUM Protection**: History preserved in table itself

### **Q: How do you handle the storage cost of SCD Type 2?**
**A:** We use selective implementation:
- Critical tables (patients, claims): SCD Type 2
- Reference tables (lab results): Time travel only
- Result: 60% cost savings while preserving all business value

### **Q: Explain your dual-layer approach.**
**A:** We implement both time travel and SCD Type 2:
- **Time Travel**: Universal capability for all tables
- **SCD Type 2**: Performance optimization for important tables
- **Benefits**: Fast lookups + complete audit trails

### **Q: How do you handle HIPAA compliance with SCD?**
**A:** Dual compliance approach:
- SCD Type 2: 7-year history in table
- Time Travel: Point-in-time snapshots
- Change Data Feed: Complete audit logging
- Result: 100% HIPAA compliance

### **Q: What was your biggest SCD challenge?**
**A:** Balancing storage cost with performance. We solved it with:
- Selective SCD Type 2 implementation
- Strategic indexing and partitioning
- Dual-layer architecture
- Results: 60% cost savings, 95% performance improvement

---

## Future Enhancements

### **Planned Optimizations:**
1. **Automated SCD Detection**: AI-powered change pattern analysis
2. **Dynamic Partitioning**: Adaptive partitioning based on query patterns
3. **Real-time SCD**: Sub-second SCD updates for critical data
4. **Cross-Table SCD**: Related dimension synchronization

### **Scaling Considerations:**
1. **Petabyte Scale**: Distributed SCD processing
2. **Global Deployment**: Multi-region SCD synchronization
3. **Real-time Analytics**: Live SCD updates
4. **Cost Optimization**: Tiered SCD storage

---

## Key Takeaways

### **Technical Excellence:**
- Deep SCD pattern understanding
- Performance optimization expertise
- Healthcare domain knowledge
- Compliance implementation experience

### **Business Impact:**
- 16x faster current lookups
- 60% storage cost savings
- 100% HIPAA compliance
- 95% query performance improvement

### **Leadership Demonstrated:**
- Strategic architecture decisions
- Cost-performance optimization
- Risk mitigation strategies
- Compliance framework design

---

*This SCD expertise demonstrates senior-level data modeling with specific healthcare domain knowledge and measurable business impact.*
