# CleanSales Backend Task Management

## Priority 1: Critical Issues & Bugs

### Bug Fixes (Immediate)
- [ ] **URGENT**: Fix batch_name task lookup issue - some batch names not finding tasks
  - Case: "山上黑-陳世平25'0304" returns no tasks when tasks should exist
  - Investigate potential issues:
    - [ ] Character encoding problems (quotes, special characters)
    - [ ] Label matching logic in Todoist API calls
    - [ ] Cache invalidation for specific batch names
    - [ ] Database query matching (exact vs fuzzy matching)
    - [ ] API rate limiting causing incomplete results

## Priority 2: Performance & Infrastructure

### Database Connection Consolidation
- ✅ Created `get_db_connection()` function in `src/db_init.py`
- ✅ Added `get_db_connection_context()` context manager
- ✅ Migrated `TodoistCacheService` to use centralized connection
- ✅ Added todoist_cache table creation to main `init_db()`
- ✅ Optimized database connection API with WAL mode and simplified parameters
- ✅ Removed unnecessary threading locks and timeout configurations
- ✅ Simplified `TodoistCacheService` by removing singleton pattern
- ✅ Replaced `SELECT *` with explicit column names for better maintainability
- ✅ Removed redundant cursor operations and manual commits
- ✅ Test all database operations work correctly
- [ ] **REMAINING**: Replace direct `sqlite3.connect()` calls in remaining files:
  - [ ] Update `src/server/batches_route.py`
  - [ ] Update `src/server/upload_route.py`
  - [ ] Update `src/upload_handlers.py`

### Todoist Service Performance Optimization
- [ ] **HIGH**: Separate fast `get_tasks()` and slow `get_completed_tasks()` operations
- [ ] Implement independent caching strategies for active vs completed tasks
- [ ] Add background task for completed tasks fetching
- [ ] Add separate cache expiration times (active: shorter, completed: longer)
- [ ] Consider pagination for large completed task sets

## Priority 3: Core Functionality

### Essential Backend APIs
- [ ] Fix existing Todoist API integration issues
- [ ] Improve error handling and logging for API failures
- [ ] Add proper validation for batch names and task data

### Basic Task Management
- [ ] Ensure reliable task creation via existing APIs
- [ ] Verify task status updates work correctly
- [ ] Test task deletion functionality

## Priority 4: Code Quality & Maintenance

### Code Improvements
- [ ] Add comprehensive error logging for debugging
- [ ] Improve API response consistency
- [ ] Add input validation and sanitization
- [ ] Update documentation for new database connection patterns

### Testing
- [ ] Add tests for bug fixes
- [ ] Verify performance improvements with larger datasets
- [ ] Test character encoding edge cases

## Archived/Future Items

### UI Enhancements (Lower Priority)
- Task creation forms
- Inline editing
- Filtering and sorting
- Bulk operations
- Advanced UI features

### Future Considerations
- Task assignments
- File attachments
- Email notifications
- Mobile app support

## Success Criteria (Current Focus)

1. **Bug Resolution**: "山上黑-陳世平25'0304" and similar batch names find tasks correctly
2. **Performance**: Fast loading of active tasks, background loading of completed tasks
3. **Reliability**: Consistent API responses and proper error handling
4. **Maintainability**: Clean database connection patterns across all files

## Notes

- Focus on fixing existing issues before adding new features
- Performance optimization is crucial for user experience
- Database consolidation must be completed for maintainability
- UI enhancements are secondary to core functionality reliability