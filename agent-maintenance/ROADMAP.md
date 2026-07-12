# RSSForge Roadmap

## Q3 2026 (Jul-Sep)

### July 2026
**Theme**: Stability & Reliability

**Week 2 (Current)**:
- [ ] Verify 36 suspected down feeds (ISSUE-001)
- [ ] Fix recoverable parsers
- [ ] Remove dead domains
- [ ] Achieve 50%+ feed health ratio

**Week 3**:
- [ ] Implement full-text extraction (ISSUE-002)
  - Phase 1: Config flag in `sites.yaml`
  - Phase 2: Engine modifications
  - Phase 3: Deploy to top 5 feeds

**Week 4**:
- [ ] Parser audit and updates (ISSUE-004)
- [ ] Performance baseline measurements
- [ ] Documentation sprint

---

### August 2026
**Theme**: Performance & Scale

**Week 1**:
- [ ] Parallel crawling implementation
- [ ] Smart caching layer
- [ ] Reduce crawl time to <5 minutes

**Week 2**:
- [ ] Add 10 new high-quality feeds
- [ ] Implement delta updates
- [ ] Optimize storage

**Week 3-4**:
- [ ] Alerting system (ISSUE-003)
- [ ] User notification system
- [ ] Dashboard prototype

---

### September 2026
**Theme**: Quality & UX

**Week 1-2**:
- [ ] Content quality filters
- [ ] Duplicate detection
- [ ] Feed categorization

**Week 3-4**:
- [ ] User feedback integration
- [ ] Custom feed builder
- [ ] API documentation

---

## Q4 2026 (Oct-Dec)

### October 2026
**Theme**: Advanced Features

- [ ] Machine learning for content ranking
- [ ] Sentiment analysis
- [ ] Trending topics detection
- [ ] Mobile-optimized feeds

### November 2026
**Theme**: Integration & Ecosystem

- [ ] Webhook notifications
- [ ] Third-party integrations
- [ ] Browser extension
- [ ] Mobile app prototype

### December 2026
**Theme**: Year-End Review

- [ ] Performance retrospective
- [ ] User satisfaction survey
- [ ] 2027 planning
- [ ] Holiday freeze (minimal changes)

---

## Backlog (No Target Date)

### Features
- [ ] Multi-language support
- [ ] Podcast feed support
- [ ] YouTube channel monitoring
- [ ] Social media aggregation
- [ ] Real-time push notifications

### Infrastructure
- [ ] Kubernetes deployment
- [ ] Multi-region redundancy
- [ ] CDN for feed delivery
- [ ] Automated testing pipeline

### Research
- [ ] Study PolitePol architecture
- [ ] Analyze Morss.it parsing
- [ ] Evaluate RSS-Bridge connectors
- [ ] Survey competitor features

---

## Technical Debt

### High Priority
- [ ] Refactor parser system (modular design)
- [ ] Add comprehensive test coverage
- [ ] Improve error handling
- [ ] Code documentation

### Medium Priority
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance profiling
- [ ] Memory leak detection

### Low Priority
- [ ] Code style consistency
- [ ] Remove deprecated functions
- [ ] Optimize imports
- [ ] Clean up TODO comments

---

## Success Metrics

### System Health
- **Current**: 25% feed health
- **Target**: >90% feed health
- **Metric**: `healthy_feeds / total_feeds`

### Performance
- **Current**: ~15 min crawl time
- **Target**: <5 min crawl time
- **Metric**: Average job duration

### User Value
- **Current**: 48 feeds
- **Target**: 100 feeds
- **Metric**: Active feed count

### Reliability
- **Current**: Manual checks
- **Target**: 99.9% uptime
- **Metric**: Actions success rate

---

## Decision Framework

### Adding New Feeds
1. **Value**: Does it provide unique content?
2. **Reliability**: Is the site stable?
3. **Legal**: Is scraping allowed?
4. **Maintenance**: Can we maintain the parser?

### Removing Feeds
1. **Dead**: Domain no longer exists
2. **Unfixable**: Parser broken, no alternative
3. **Low value**: Content not useful
4. **Legal**: Cease-and-desist received

### Prioritizing Work
1. **P0**: System down, data loss, security issue
2. **P1**: Major feature, significant user impact
3. **P2**: Improvements, optimizations
4. **P3**: Nice-to-have, polish

---

## Review Schedule

- **Weekly**: Progress check (Sunday 23:00)
- **Monthly**: Roadmap review (1st of month)
- **Quarterly**: Strategic planning (1st of quarter)
- **Annually**: Year retrospective (January)

---

**Last Updated**: 2026-07-11
**Next Review**: 2026-07-12 23:00
