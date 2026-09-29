# Official source notes

These references were checked on 2026-09-29. They support design assumptions but are not
legal advice and do not replace reviewing source terms or obtaining counsel.

## CSLB

- [CSLB Public Data Portal](https://www.cslb.ca.gov/Onlineservices/DataPortal/) offers public
  contractor lists, a master list, and instant license check.
- [CSLB web service registration](https://www.cslb.ca.gov/Onlineservices/DataPortal/register)
  shows registration for access to the license-data web service and requests host/IP details.
- [CSLB forms and data files](https://www.cslb.ca.gov/About_Us/Library/Forms_And_Applications.aspx)
  describes paid full/update files, their cadence, scope, and record counts. It notes that the
  license master contains bond information but not workers' compensation, so feed-field
  validation is a launch prerequisite.
- [CSLB home-improvement contract guidance](https://www.cslb.ca.gov/Consumers/Hire_A_Contractor/Home_Improvement_Contracts/What_Is_A_Contract.aspx)
  states that written contracts are required for California home-improvement work over $500,
  describes written payment schedules/change orders, and states the general down-payment cap.

## California privacy

- [California DOJ CCPA page](https://www.oag.ca.gov/privacy/ccpa) summarizes rights to know,
  delete, opt out, correct, limit, and nondiscrimination; notices at collection; and current
  applicability thresholds. The architecture implements these workflows conservatively even
  if the launch company is initially below a statutory threshold.

## AWS

- [Scheduling Amazon ECS tasks](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/scheduling_tasks.html)
  documents service, standalone, and scheduled ECS tasks.
- [EventBridge Scheduler for ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/tasks-scheduled-eventbridge-scheduler.html)
  documents recurring Fargate tasks, retries, roles, and DLQ options used by the CSLB job.
- [ECS deployment strategies](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_service-options.html)
  documents replica services and Availability Zone spreading.

## Anthropic

- [Claude API overview](https://platform.claude.com/docs/en/api/overview) documents the
  Messages API, authentication, workspaces, rate limits, and official SDKs.
- [Claude authentication](https://platform.claude.com/docs/en/manage-claude/authentication)
  recommends secret-manager storage and periodic key rotation, and describes service-account
  keys and Workload Identity Federation.
- [Claude API data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
  describes retention behavior and should be rechecked against the organization's contracted
  terms before any production data is sent.
