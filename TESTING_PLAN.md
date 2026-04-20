# Testing Plan for xiaokeda2 (小可大) Application

## Project Overview

**Project:** xiaokeda2 - AI-powered tutoring platform for Chinese primary school students
**Type:** Flask Web Application
**Database:** SQLite with SQLAlchemy ORM
**AI Integration:** OpenAI-compatible API (supports MiniMax)

## Current Testing Status

### Existing Tests (39 tests)
- **Location:** `/root/xiaokeda2/tests/`
- **Framework:** pytest
- **Test Files:**
  - `test_ai_service.py` - AI service unit tests (5 tests)
  - `test_forms.py` - Form validation tests (7 tests)
  - `test_integration.py` - Integration tests (21 tests)
  - `test_security.py` - Security tests (4 tests)
  - `ui_test.py` - Playwright UI tests (requires installation)

### Test Results
- **Before Flask-WTF installation:** 39 tests PASSED
- **After Flask-WTF installation:** 6 tests FAIL (pre-existing bugs exposed)

## Bugs Identified

### Bug 1: CSRF Template Issue (HIGH PRIORITY)
**Location:** `app/templates/base.html` line 6
```html
<meta name="csrf-token" content="{{ csrf_token() }}">
```
**Issue:** Template unconditionally calls `csrf_token()` which requires SECRET_KEY.
**Impact:** Tests fail with "A secret key is required to use CSRF" when CSRF is disabled but templates still render.
**Fix:** Check if CSRF is enabled before rendering token, or ensure SECRET_KEY is always set.

### Bug 2: Homework Status Update Logic Error (MEDIUM PRIORITY)
**Location:** `app/routes/homework.py` line 149
```python
homework.status = new_status  # Line 146
...
if new_status == 'completed' and homework.status != 'completed':  # Line 149
```
**Issue:** Condition checks `homework.status != 'completed'` AFTER assignment, so it's always True when new_status='completed'.
**Impact:** Multiple study sessions may be created when marking homework as completed repeatedly.
**Fix:** Save old status before assignment:
```python
old_status = homework.status
homework.status = new_status
if new_status == 'completed' and old_status != 'completed':
    # create study session
```

### Bug 3: PDF Service Test Assertion Error (LOW PRIORITY)
**Location:** `tests/test_integration.py` line 311
```python
assert '答案' not in cleaned  # Wrong expectation
```
**Issue:** Test expects '答案' to be removed, but the cleaning logic keeps answer labels.
**Actual:** Cleaned text contains '答案：' which is correct behavior.
**Fix:** Update test expectation to:
```python
assert '5分' not in cleaned  # Score removed, but answer label kept
```

### Bug 4: Deprecated API Usage (TECHNICAL DEBT)
**Locations:** Multiple files
- `datetime.utcnow()` - Deprecated, use `datetime.now(datetime.UTC)`
- `Query.get()` - Deprecated, use `Session.get()`

## Comprehensive Testing Plan

### Phase 1: Unit Tests (Current Gaps)

#### 1.1 Model Tests
- [ ] Student model: Avatar handling, relationship cascade deletes
- [ ] Homework model: `mistake_count` property edge cases
- [ ] Mistake model: Spaced repetition intervals boundary conditions
- [ ] ReviewPlan model: Progress percentage with 0 tasks
- [ ] ReviewTask model: JSON parsing of `mistake_ids`

#### 1.2 Service Tests
- [ ] `review_engine.auto_generate_plan()`: Edge case when no mistakes exist
- [ ] `review_engine.complete_task()`: Task not found handling
- [ ] `stats_service.get_weak_areas()`: Empty result handling
- [ ] `stats_service.get_subject_comparison()`: Student not found
- [ ] `ai_service._call_vision()`: API failure handling
- [ ] `ai_service._call_text()`: Timeout handling
- [ ] `pdf_service._clean_question_text()`: Various text formats

#### 1.3 Form Tests
- [ ] StudentForm: Name with special characters
- [ ] HomeworkForm: Date validation (future/past dates)
- [ ] MistakeForm: All difficulty levels
- [ ] ReviewPlanForm: Exam date validation (must be in future)

### Phase 2: Integration Tests

#### 2.1 Route Tests
- [ ] All routes return proper HTTP status codes
- [ ] Routes redirect when student not selected
- [ ] Routes return 404 for non-existent resources
- [ ] Routes enforce student ownership

#### 2.2 Workflow Tests
- [ ] Student registration → Homework creation → Mistake extraction
- [ ] Review plan creation → Task completion → Progress tracking
- [ ] Material upload → AI analysis → Question generation

#### 2.3 API JSON Tests
- [ ] `/homework/<id>/items` (POST/PUT)
- [ ] `/mistakes/<id>/mark-reviewed` (POST)
- [ ] `/review/plan/<id>/task/<tid>/complete` (POST)
- [ ] `/materials/browse/api/list` (GET)
- [ ] `/reports/api/*` endpoints

### Phase 3: Security Tests

#### 3.1 Input Validation
- [ ] XSS prevention in all user inputs
- [ ] SQL injection prevention (using SQLAlchemy ORM)
- [ ] File upload validation (extension, size)
- [ ] Path traversal prevention in materials browse

#### 3.2 Access Control
- [ ] Students can only access their own data
- [ ] Routes properly redirect unauthorized access
- [ ] API endpoints return 403 for unauthorized access

#### 3.3 CSRF Protection
- [ ] POST requests require CSRF token
- [ ] CSRF token is properly validated
- [ ] Templates handle missing CSRF gracefully

### Phase 4: UI Tests (Playwright)

#### 4.1 Page Load Tests
- [ ] Homepage loads without student
- [ ] Homepage loads with student
- [ ] Settings page loads
- [ ] All navigation links work

#### 4.2 Functional UI Tests
- [ ] Student profile creation
- [ ] Homework creation with photo upload
- [ ] Mistake marking as reviewed
- [ ] Review plan progress tracking

#### 4.3 Browser Compatibility
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Mobile viewport

### Phase 5: Performance Tests

#### 5.1 Load Tests
- [ ] Homepage with many students
- [ ] Dashboard with large homework history
- [ ] Reports with large data sets

#### 5.2 AI Service Tests
- [ ] API response time under load
- [ ] Rate limiting handling
- [ ] API key validation

## Test Execution Commands

```bash
# Run all unit tests
cd /root/xiaokeda2
python3 -m pytest tests/ -v --ignore=tests/ui_test.py

# Run specific test file
python3 -m pytest tests/test_integration.py -v

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=html

# Run UI tests (requires Playwright)
python3 -m pytest tests/ui_test.py
playwright install chromium
```

## Dependencies for Testing

```bash
pip install pytest pytest-cov pytest-flask
pip install playwright
playwright install chromium
pip install httpx requests-mock
```

## Notes

1. The CSRF template bug is a HIGH priority fix - it prevents all form-rendering routes from working in tests.

2. The homework status update bug should be verified with a test that marks homework as completed twice.

3. All tests currently use SQLite in-memory database for isolation.

4. The UI test requires a running Flask server on localhost:5000.

5. The project uses legacy SQLAlchemy APIs that should be migrated to modern equivalents for long-term support.