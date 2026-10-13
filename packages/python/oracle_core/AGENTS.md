# Core rules

Read the root instructions and architecture boundaries. Core is shared infrastructure,
not a dumping ground. Add an abstraction only for demonstrated consumers or an
immediately required use case. Keep interfaces free of game mechanics and do not
assume every domain has the same runtime requirements.

Favor simple replaceable adapters and portable locally testable components. Keep
persistence details out of generic business contracts when useful. Core must not
import domains or applications. Avoid complex infrastructure before workloads need it.

Runs, workers and artifacts are the accepted early direction when needed. PostgreSQL,
a Python worker and replaceable artifact storage are provisional choices for the first
real workload. Do not implement them merely to validate a scaffold.
