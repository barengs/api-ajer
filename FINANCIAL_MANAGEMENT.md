# Financial Management Module

## Overview

The Financial Management Module provides comprehensive financial dashboards and management tools for administrators and instructors in the Hybrid LMS platform. This module offers real-time analytics, reporting capabilities, and payout management features.

## Features

### For Administrators

1. **Financial Dashboard**

   - Platform revenue analytics
   - Order and payment statistics
   - Refund tracking
   - Instructor payout summaries
   - Coupon performance metrics
   - Top performing courses and instructors

2. **Detailed Reporting**

   - Revenue reports by time period
   - Payout reports by instructor
   - Refund analysis
   - Course performance reports
   - Export options (JSON, CSV)

3. **Manual Payout Processing**
   - Process instructor payouts manually
   - Track payout history
   - Update revenue records

### For Instructors

1. **Personal Financial Dashboard**
   - Earnings analytics
   - Course-specific sales data
   - Payout history and status
   - Revenue trends over time
   - Enrollment trends

## API Endpoints

### Admin Endpoints

| Endpoint                                      | Method | Description                |
| --------------------------------------------- | ------ | -------------------------- |
| `/api/v1/payments/financial/admin/dashboard/` | GET    | Admin financial dashboard  |
| `/api/v1/payments/admin/reports/`             | GET    | Generate financial reports |
| `/api/v1/payments/admin/payouts/process/`     | POST   | Process instructor payouts |

### Instructor Endpoints

| Endpoint                                           | Method | Description                    |
| -------------------------------------------------- | ------ | ------------------------------ |
| `/api/v1/payments/financial/instructor/dashboard/` | GET    | Instructor financial dashboard |

## Time Period Filters

All dashboard endpoints support the following time period filters:

- `today`
- `yesterday`
- `this_week`
- `last_week`
- `this_month`
- `last_month`
- `this_quarter`
- `this_year`
- `last_year`
- `custom_range` (requires `start_date` and `end_date` parameters)

## Report Types

Admin reports support the following report types:

1. **Revenue Report** (`revenue`)

   - Platform revenue breakdown
   - Orders and conversion metrics
   - Daily/weekly/monthly trends

2. **Payout Report** (`payouts`)

   - Instructor payout summary
   - Payment method distribution
   - Payout history

3. **Refund Report** (`refunds`)

   - Refund analysis
   - Reason breakdown
   - Trend analysis

4. **Course Performance Report** (`courses`)
   - Course-specific revenue data
   - Sales performance
   - Enrollment metrics

## Management Commands

### Generate Financial Reports

```bash
python manage.py generate_financial_report --type revenue --period monthly --format json
```

**Parameters:**

- `--type`: Report type (revenue, payouts, refunds, courses)
- `--period`: Time period (daily, weekly, monthly, quarterly, yearly)
- `--start-date`: Custom start date (YYYY-MM-DD)
- `--end-date`: Custom end date (YYYY-MM-DD)
- `--format`: Output format (json, csv)
- `--output`: Output file name

## Data Models

### Revenue Tracking

The module extends the existing payment models with additional financial tracking capabilities:

1. **Revenue Model**

   - Tracks earnings per order item
   - Links to instructor payouts
   - Commission calculations

2. **InstructorPayout Model**
   - Payout period management
   - Payment method tracking
   - Status tracking

## Security

- All endpoints require authentication
- Admin endpoints require staff permissions
- Instructor endpoints are role-restricted
- Data access is limited to authorized users only

## Implementation Details

### Admin Financial Dashboard

The admin dashboard provides a comprehensive overview of platform financials:

1. **Revenue Summary**

   - Total revenue
   - Platform commission
   - Instructor earnings
   - Net platform revenue

2. **Order Metrics**

   - Total orders
   - Completed orders
   - Conversion rate
   - Average order value

3. **Payment Metrics**

   - Total payments
   - Successful payments
   - Failed payments
   - Success rate

4. **Refund Metrics**

   - Total refunds
   - Refund amount
   - Refund rate

5. **Performance Data**
   - Top performing courses
   - Top performing instructors

### Instructor Financial Dashboard

The instructor dashboard provides personal financial insights:

1. **Earnings Summary**

   - Total earnings
   - Pending payouts
   - Paid out amounts
   - Courses sold

2. **Course Performance**

   - Revenue per course
   - Sales data
   - Enrollment metrics

3. **Payout History**

   - Recent payouts
   - Payout status
   - Payment details

4. **Enrollment Trends**
   - Daily enrollment counts
   - Trend visualization

## Usage Examples

### Accessing Admin Dashboard

```bash
curl -X GET "http://localhost:8000/api/v1/payments/financial/admin/dashboard/?period=this_month" \
     -H "Authorization: Bearer <access_token>"
```

### Generating Revenue Report

```bash
curl -X GET "http://localhost:8000/api/v1/payments/admin/reports/?report_type=revenue&period=monthly" \
     -H "Authorization: Bearer <access_token>"
```

### Processing Instructor Payout

```bash
curl -X POST "http://localhost:8000/api/v1/payments/admin/payouts/process/" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{
           "instructor_id": 1,
           "period_start": "2024-01-01",
           "period_end": "2024-01-31",
           "amount": "5000000.00",
           "payout_method": "bank_transfer",
           "notes": "January 2024 payout"
         }'
```

## Testing

The module includes comprehensive tests covering:

1. Dashboard access permissions
2. Report generation functionality
3. Payout processing
4. Date filtering
5. Data validation

Run tests with:

```bash
python manage.py test payments.tests.FinancialManagementTestCase
```

## Future Enhancements

1. **Advanced Analytics**

   - Predictive revenue modeling
   - Instructor performance forecasting
   - Market trend analysis

2. **Enhanced Reporting**

   - Custom report builder
   - Scheduled report generation
   - Automated report delivery

3. **Integration Features**

   - Accounting software integration
   - Tax reporting tools
   - Multi-currency support

4. **Visualization**
   - Interactive dashboards
   - Chart and graph visualization
   - Export to PDF/Excel

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**

   - Ensure user has appropriate role (admin/instructor)
   - Verify authentication token is valid

2. **Date Format Errors**

   - Use YYYY-MM-DD format for date parameters
   - Ensure start date is before end date

3. **Invalid Report Types**
   - Check supported report types in documentation
   - Verify spelling and case sensitivity

### Support

For issues with the financial management module, contact the development team or check the system logs for detailed error information.
