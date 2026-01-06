# Campus Issue Reporting System - Architecture Documentation

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────┐    HTTP/HTTPS    ┌──────────────────┐
│                 │◄─────────────────►│                  │
│   Web Browser   │                  │  S3 Static Web   │
│   (User)        │                  │     Hosting      │
│                 │                  │  (Frontend)      │
└─────────────────┘                  └──────────────────┘
                                               │
                                               │ REST API Calls
                                               ▼
                                    ┌──────────────────┐
                                    │                  │
                                    │  API Gateway     │
                                    │  (REST API)      │
                                    │                  │
                                    └──────────────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                              ▼                ▼                ▼
                    ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
                    │                 │ │             │ │              │
                    │ Lambda:         │ │ Lambda:     │ │ Lambda:      │
                    │ CreateIssue     │ │ GetIssue    │ │ UpdateStatus │
                    │                 │ │             │ │              │
                    └─────────────────┘ └─────────────┘ └──────────────┘
                              │                │                │
                              └────────────────┼────────────────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │                  │
                                    │    DynamoDB      │
                                    │  (CampusIssues   │
                                    │     Table)       │
                                    └──────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                      Additional Services                            │
    │  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐ │
    │  │                  │    │                  │    │                │ │
    │  │       SES        │    │   CloudWatch     │    │      IAM       │ │
    │  │ (Email Notify)   │    │    (Logging)     │    │   (Security)   │ │
    │  │                  │    │                  │    │                │ │
    │  └──────────────────┘    └──────────────────┘    └────────────────┘ │
    └─────────────────────────────────────────────────────────────────────┘
```

## 🔧 Component Details

### 1. Frontend Layer (S3 Static Website)

**Technology:** HTML5, CSS3, Vanilla JavaScript
**Purpose:** User interface for issue reporting and status checking
**Features:**

- Responsive design
- Form validation
- Real-time status updates
- Admin interface for status updates

**Files:**

- `index.html` - Complete web application

### 2. API Layer (API Gateway)

**Type:** REST API
**Purpose:** Handles HTTP requests and routes to appropriate Lambda functions

**Endpoints:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/report-issue` | Create new issue |
| GET | `/issue-status/{issueId}` | Get issue details |
| PUT | `/update-status` | Update issue status (Admin) |

**Features:**

- CORS enabled
- Lambda proxy integration
- Request/response transformation
- Error handling

### 3. Business Logic Layer (Lambda Functions)

#### 3.1 CreateIssue Function

**Runtime:** Python 3.11
**Purpose:** Process new issue submissions
**Functionality:**

- Generate unique issue ID
- Validate input data
- Store issue in DynamoDB
- Send email notification via SES
- Return issue ID to user

#### 3.2 GetIssue Function

**Runtime:** Python 3.11
**Purpose:** Retrieve issue details by ID
**Functionality:**

- Query DynamoDB by issue ID
- Return issue details
- Handle not found scenarios

#### 3.3 UpdateStatus Function

**Runtime:** Python 3.11
**Purpose:** Update issue status (Admin function)
**Functionality:**

- Update issue status in DynamoDB
- Send status change notification via SES
- Return confirmation

### 4. Data Layer (DynamoDB)

#### Table: CampusIssues

**Billing Mode:** On-demand
**Partition Key:** issueId (String)

**Attributes:**
| Attribute | Type | Purpose |
|-----------|------|---------|
| issueId | String | Unique identifier (UUID) |
| issueType | String | Category of issue |
| description | String | Issue details |
| location | String | Where the issue occurred |
| status | String | OPEN/IN_PROGRESS/RESOLVED |
| createdAt | String | ISO timestamp |

### 5. Notification Layer (SES)

**Purpose:** Email notifications for issues and status updates
**Configuration:** Sandbox mode (verified emails only)
**Features:**

- New issue notifications
- Status update notifications
- Plain text format

### 6. Security Layer (IAM)

#### IAM Role: CampusIssueLambdaRole

**Attached Policies:**

1. `AWSLambdaBasicExecutionRole` (AWS Managed)
2. Custom inline policy for DynamoDB and SES access

**Permissions:**

```json
{
  "DynamoDB": ["PutItem", "GetItem", "UpdateItem"],
  "SES": ["SendEmail"],
  "CloudWatch": ["CreateLogGroup", "CreateLogStream", "PutLogEvents"]
}
```

### 7. Monitoring Layer (CloudWatch)

**Purpose:** Logging and monitoring
**Features:**

- Automatic log collection from Lambda
- Error tracking
- Performance metrics
- Audit trail

## 📊 Data Flow Diagrams

### New Issue Submission Flow

```
1. User fills form → 2. Frontend validates → 3. POST to API Gateway
                                                         ↓
8. Display Issue ID ← 7. Return response ← 6. Lambda response ← 4. Lambda: CreateIssue
                                                         ↓
                                                  5a. Store in DynamoDB
                                                         ↓
                                                  5b. Send email via SES
```

### Issue Status Check Flow

```
1. User enters Issue ID → 2. GET request to API Gateway → 3. Lambda: GetIssue
                                    ↑                             ↓
5. Display issue details ← 4. Return issue data ← Query DynamoDB
```

### Status Update Flow (Admin)

```
1. Admin updates status → 2. PUT to API Gateway → 3. Lambda: UpdateStatus
                                   ↑                         ↓
6. Confirmation message ← 5. Return response ← 4a. Update DynamoDB
                                                         ↓
                                                4b. Send notification email
```

## 🔒 Security Architecture

### 1. Authentication & Authorization

- **Current:** No authentication (demo system)
- **Recommended:** AWS Cognito for user management
- **Admin Access:** Should be protected in production

### 2. Data Protection

- **Encryption at Rest:** DynamoDB default encryption
- **Encryption in Transit:** HTTPS/TLS for all communications
- **Access Control:** IAM policies with least privilege

### 3. Network Security

- **API Gateway:** Regional endpoint
- **S3:** Public read-only access for website
- **Lambda:** VPC not required (using AWS managed services)

### 4. Input Validation

- **Frontend:** Client-side validation
- **Backend:** Lambda function validation
- **Database:** Type constraints in DynamoDB

## 🚀 Scalability Considerations

### Current Capacity

| Component       | Limit                      | Scalability          |
| --------------- | -------------------------- | -------------------- |
| **Lambda**      | 1000 concurrent executions | Auto-scales          |
| **API Gateway** | 10,000 requests/second     | Auto-scales          |
| **DynamoDB**    | On-demand                  | Auto-scales          |
| **S3**          | Unlimited                  | Auto-scales          |
| **SES**         | 200 emails/day (sandbox)   | Requestable increase |

### Performance Optimizations

1. **Lambda Cold Start:** Use provisioned concurrency if needed
2. **DynamoDB:** Consider Global Secondary Indexes for queries
3. **API Gateway:** Enable caching for GET requests
4. **S3:** Use CloudFront CDN for global distribution

## 🔄 Deployment Architecture

### Environments

- **Development:** Local testing with AWS CLI
- **Production:** Direct deployment to AWS Free Tier

### CI/CD Considerations

- **Source Control:** Git repository
- **Deployment:** Manual deployment (suitable for demo)
- **Future:** AWS CodePipeline for automation

## 📈 Cost Architecture

### AWS Free Tier Usage

| Service     | Monthly Limit      | Expected Usage | Cost  |
| ----------- | ------------------ | -------------- | ----- |
| Lambda      | 1M requests        | < 1K requests  | $0.00 |
| DynamoDB    | 25GB + 25 RCU/WCU  | < 1GB          | $0.00 |
| API Gateway | 1M calls           | < 1K calls     | $0.00 |
| S3          | 5GB + 20K requests | < 1MB          | $0.00 |
| SES         | 62K emails         | < 100 emails   | $0.00 |

**Total Monthly Cost: $0.00**

## 🔮 Future Architecture Enhancements

### Phase 1: Authentication

- Add AWS Cognito User Pools
- JWT token-based authentication
- Role-based access control

### Phase 2: Real-time Features

- WebSocket API for real-time updates
- Push notifications to mobile devices
- Live chat support

### Phase 3: Analytics & Reporting

- Add analytics dashboard
- Issue trend analysis
- Performance metrics
- Custom reporting

### Phase 4: Integration

- Connect with existing campus systems
- LDAP integration for user management
- Third-party notification services
- Mobile application

## 🛠️ Technology Stack Summary

| Layer          | Technology               | Purpose                |
| -------------- | ------------------------ | ---------------------- |
| **Frontend**   | HTML5, CSS3, JavaScript  | User interface         |
| **API**        | AWS API Gateway          | REST API management    |
| **Backend**    | AWS Lambda (Python 3.11) | Business logic         |
| **Database**   | AWS DynamoDB             | Data storage           |
| **Storage**    | AWS S3                   | Static website hosting |
| **Email**      | AWS SES                  | Email notifications    |
| **Security**   | AWS IAM                  | Access management      |
| **Monitoring** | AWS CloudWatch           | Logging and metrics    |

This architecture provides a robust, scalable, and cost-effective solution for campus issue reporting while remaining within AWS Free Tier limits.
