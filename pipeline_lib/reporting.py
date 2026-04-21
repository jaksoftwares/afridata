# =============================================================================
# pipeline_reporting.py — DATA QUALITY REPORTING
# =============================================================================

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# COMPREHENSIVE DATA QUALITY REPORT
# =============================================================================
def generate_data_quality_report(original_df, final_df, schema, cleaning_results):
    """Generate a one-page summary report of all cleaning operations"""
    
    report = {
        "summary": {
            "original_rows": original_df.height,
            "final_rows": final_df.height,
            "total_rows_removed": original_df.height - final_df.height,
            "rows_removed_pct": round((original_df.height - final_df.height) / original_df.height * 100, 2) if original_df.height > 0 else 0,
            "columns": len(schema)
        },
        "operations_summary": {
            "null_handling": cleaning_results.get('null_handling', {}).get('rows_removed', 0),
            "duplicates_removed": cleaning_results.get('deduplication', {}).get('removed', 0),
            "outliers_detected": cleaning_results.get('outliers', {}).get('total_outliers', 0),
            "validation_errors": cleaning_results.get('validation', {}).get('invalid_rows', 0),
            "pattern_issues": cleaning_results.get('patterns', {}).get('total_pattern_issues', 0),
            "integrity_issues": cleaning_results.get('integrity', {}).get('total_integrity_issues', 0)
        },
        "data_quality": {
            "avg_completeness": round(
                sum(q.get('completeness', 0) for q in cleaning_results.get('quality', [])) / 
                len(cleaning_results.get('quality', [1])), 1
            ),
            "columns_with_nulls": sum(
                1 for col, stats in 
                cleaning_results.get('null_handling', {}).get('null_stats', {}).items()
                if stats.get('after_null_pct', 0) > 0
            ),
            "columns_with_outliers": len(cleaning_results.get('outliers', {}).get('outlier_stats', {}))
        },
        "issues_found": {
            "null_values": cleaning_results.get('null_handling', {}).get('null_stats', {}),
            "outliers": cleaning_results.get('outliers', {}).get('outlier_stats', {}),
            "validation_errors": cleaning_results.get('validation', {}).get('validation_errors', {}),
            "pattern_issues": cleaning_results.get('patterns', {}).get('pattern_issues', {}),
            "integrity_issues": cleaning_results.get('integrity', {}).get('integrity_issues', {})
        }
    }
    
    return report

# =============================================================================
# FORMATTED REPORT PRINTING
# =============================================================================
def print_data_quality_report(report):
    """Print a formatted one-page data quality report"""
    
    print("\n" + "="*80)
    print("📊 DATA QUALITY REPORT — ONE PAGE SUMMARY".center(80))
    print("="*80 + "\n")
    
    # SUMMARY SECTION
    summary = report['summary']
    print("┌─ DATASET OVERVIEW ".ljust(80, "─") + "┐")
    print(f"│ Original Rows       : {summary['original_rows']:,}".ljust(80) + "│")
    print(f"│ Final Rows          : {summary['final_rows']:,}".ljust(80) + "│")
    print(f"│ Total Removed       : {summary['total_rows_removed']:,} ({summary['rows_removed_pct']}%)".ljust(80) + "│")
    print(f"│ Columns Processed   : {summary['columns']}".ljust(80) + "│")
    print("└" + "─"*78 + "┘\n")
    
    # OPERATIONS SUMMARY
    ops = report['operations_summary']
    print("┌─ CLEANING OPERATIONS PERFORMED ".ljust(80, "─") + "┐")
    print(f"│ ✓ Null Value Handling     : {ops['null_handling']} rows cleaned".ljust(80) + "│")
    print(f"│ ✓ Deduplication          : {ops['duplicates_removed']} duplicates removed".ljust(80) + "│")
    print(f"│ ✓ Outlier Detection      : {ops['outliers_detected']} outliers found".ljust(80) + "│")
    print(f"│ ✓ Data Type Validation   : {ops['validation_errors']} validation errors".ljust(80) + "│")
    print(f"│ ✓ Pattern Validation     : {ops['pattern_issues']} pattern issues".ljust(80) + "│")
    print(f"│ ✓ Integrity Checks       : {ops['integrity_issues']} integrity issues".ljust(80) + "│")
    print("└" + "─"*78 + "┘\n")
    
    # DATA QUALITY METRICS
    quality = report['data_quality']
    print("┌─ DATA QUALITY METRICS ".ljust(80, "─") + "┐")
    print(f"│ Average Completeness (non-null) : {quality['avg_completeness']}%".ljust(80) + "│")
    print(f"│ Columns with Remaining Nulls   : {quality['columns_with_nulls']}".ljust(80) + "│")
    print(f"│ Columns with Outliers          : {quality['columns_with_outliers']}".ljust(80) + "│")
    print("└" + "─"*78 + "┘\n")
    
    # DETAILED ISSUES (if any)
    issues = report['issues_found']
    has_issues = False
    
    # Null values
    if issues.get('null_values'):
        non_empty_nulls = {k: v for k, v in issues['null_values'].items() 
                          if v.get('after_null_pct', 0) > 0}
        if non_empty_nulls:
            has_issues = True
            print("┌─ NULL VALUES REMAINING (after handling) ".ljust(80, "─") + "┐")
            for col, stats in list(non_empty_nulls.items())[:5]:
                print(f"│ {col:.<40} : {stats['after_null_pct']}%".ljust(80) + "│")
            if len(non_empty_nulls) > 5:
                print(f"│ ... and {len(non_empty_nulls)-5} more columns".ljust(80) + "│")
            print("└" + "─"*78 + "┘\n")
    
    # Outliers
    if issues.get('outliers'):
        if issues['outliers']:
            has_issues = True
            print("┌─ OUTLIERS DETECTED ".ljust(80, "─") + "┐")
            for col, stats in list(issues['outliers'].items())[:5]:
                print(f"│ {col:.<40} : {stats['outlier_count']} outliers ({stats['outlier_pct']}%)".ljust(80) + "│")
            if len(issues['outliers']) > 5:
                print(f"│ ... and {len(issues['outliers'])-5} more columns".ljust(80) + "│")
            print("└" + "─"*78 + "┘\n")
    
    # Pattern issues
    if issues.get('pattern_issues'):
        if issues['pattern_issues']:
            has_issues = True
            print("┌─ PATTERN VALIDATION ISSUES ".ljust(80, "─") + "┐")
            for col, stats in list(issues['pattern_issues'].items())[:5]:
                issue_type = stats.get('type', 'unknown')
                print(f"│ {col:.<35} ({issue_type}): {stats['invalid_count']} invalid".ljust(80) + "│")
            if len(issues['pattern_issues']) > 5:
                print(f"│ ... and {len(issues['pattern_issues'])-5} more columns".ljust(80) + "│")
            print("└" + "─"*78 + "┘\n")
    
    # Integrity issues
    if issues.get('integrity_issues'):
        if issues['integrity_issues']:
            has_issues = True
            print("┌─ REFERENTIAL INTEGRITY ISSUES ".ljust(80, "─") + "┐")
            for issue_type, stats in issues['integrity_issues'].items():
                count = stats.get('duplicate_count', stats.get('mismatch_count'))
                print(f"│ {issue_type:.<40} : {count} issues".ljust(80) + "│")
            print("└" + "─"*78 + "┘\n")
    
    if not has_issues:
        print("✅ No data quality issues detected after cleaning!\n")
    
    print("="*80)
    print("Report generated on:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80 + "\n")
