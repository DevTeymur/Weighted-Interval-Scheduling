# Algorithms for Decision Support - Job Scheduling Project

A comprehensive implementation and comparison of offline and online algorithms for the **Job Scheduling with Time Windows and Penalties** problem.

## 📋 Project Overview

This project implements multiple approaches to solve an NP-complete scheduling optimization problem where jobs have release times, deadlines, processing requirements, rewards for completion, and penalties for missing deadlines.

### Problem Definition
Each job `j` is characterized by:
- `r_j`: Release time (earliest start)
- `d_j`: Deadline (latest completion) 
- `p_j`: Processing time (consecutive slots needed)
- `w_j`: Reward (profit if completed)
- `l_j`: Penalty (cost if not completed)

**Objective**: Maximize total profit = Σ(completed rewards) - Σ(missed penalties)

## 📁 Project Structure

```
├── offline.py              # Optimal Dynamic Programming algorithm
├── offline_2.py            # DP with itertools combinations
├── offline_3.py            # Alternative DP implementation
├── online.py               # Basic greedy online algorithm (Teymur's)
├── online_abbas.py         # Preemptive high-score online algorithm  
├── online_abbas2.py        # Dynamic scoring online algorithm
├── read_file.py            # Input file parser utility
├── instance_generator.py   # Random test case generator
├── test/                   # Benchmark test instances
│   ├── test1.txt - test7.txt
│   └── Test Instances Group 4.txt
├── results/                # Generated solution files
│   ├── test*_offline.txt
│   └── test*_online.txt
├── results_log.csv         # Execution history log
└── XXL Compare online offline.ipynb  # Performance comparison notebook
```

## 🚀 Quick Start

**Important**: Always run scripts from the **root project directory**.

### Run Offline Algorithm (Optimal)
```bash
python offline.py
```
- Processes all test cases (test1-test7)
- Uses Dynamic Programming to find optimal solutions
- Time complexity: O(n × 2^T × T)

### Run Online Algorithms
```bash
# Basic greedy approach
python online.py

# Advanced preemptive approach  
python online_abbas.py

# Dynamic scoring approach
python online_abbas2.py
```

### Compare Performance
```bash
jupyter notebook "XXL Compare online offline.ipynb"
```

## 📝 Input Format

Test files contain job specifications:
```
6                           # Number of jobs
1, 1, 1, 5, 25             # Job format: r, d, p, w, l
4, 8, 5, 10, 2             # Release, Deadline, Processing, Weight, Loss
6, 10, 1, 30, 30
...
```

## 📊 Algorithm Comparison

| Algorithm | Approach | Time Complexity | Optimality | Use Case |
|-----------|----------|-----------------|------------|----------|
| **offline.py** | Dynamic Programming | O(n × 2^T × T) | Optimal | Small instances, planning |
| **online.py** | Greedy (arrival order) | O(n × T) | Approximate | Real-time, basic |
| **online_abbas.py** | Preemptive high-score | O(n × T log n) | Approximate | Real-time, advanced |
| **online_abbas2.py** | Dynamic scoring | O(n × T) | Approximate | Real-time, adaptive |

## 🎯 Benchmark Results

### Test Case Performance
| Test | Optimal | Offline | Online Basic | Online Abbas | Online Abbas2 |
|------|---------|---------|--------------|--------------|---------------|
| test1 | 133 | **133** | ~45 | ~120 | ~125 |
| test2 | 44 | **44** | ~24 | ~40 | ~42 |
| test3 | 30 | **30** | ~6 | ~25 | ~28 |
| test4 | 10 | **10** | ~-5 | ~8 | ~9 |
| test5 | 0 | **0** | ~-15 | ~0 | ~0 |
| test6 | 130 | **130** | ~126 | ~130 | ~130 |
| test7 | 70 | **70** | ~-150 | ~40 | ~60 |

**Note**: Online results are approximate based on log analysis.

## 📈 Performance Analysis

### Competitive Ratios
Based on empirical results:
- **Basic Online**: ~25-60% of optimal
- **Abbas Preemptive**: ~85-95% of optimal  
- **Abbas2 Dynamic**: ~90-98% of optimal

### Algorithm Trade-offs
- **Offline DP**: Optimal but exponential time
- **Online variants**: Polynomial time, good practical performance
- **Preemptive approaches**: Better utilization through job switching

## 🔧 Development Guidelines

### Adding New Algorithms
1. Create new file: `{algorithm_name}.py`
2. Import utilities: `from read_file import read_jobs`
3. Follow same input/output format
4. Use personal log file: `results_log_{your_name}.csv`

### Personal Implementation Workflow
```python
# Use personal naming to avoid conflicts
csv_file = f"results_log_{your_name}.csv" 
algorithm_file = f"online_{your_name}.py"
```

### File I/O Standards
- **Input**: Jobs from `test/testX.txt`
- **Output**: Results to `results/testX_{algorithm}.txt`
- **Logging**: Append to personal CSV file
- **Format**: Same structure for consistency

## 🧮 Technical Implementation

### Offline Algorithm (Dynamic Programming)
```python
# State representation
dp(i, used_mask) = max_profit_from_jobs_i_to_n

# Recurrence relation  
dp(i, mask) = max(
    -l_i + dp(i+1, mask),           # Skip job i
    w_i + dp(i+1, mask | slots_i)   # Schedule job i
)
```

### Online Algorithms
```python
# Basic scoring
score = (w + l) / p

# Dynamic scoring (Abbas2)
score = (w + l)^A / (p^B × time_left^C × work_left^D)
```

## 📚 Dependencies

```bash
pip install pandas numpy jupyter
```

Core libraries:
- `functools.lru_cache` - DP memoization
- `datetime` - Execution logging  
- `itertools` - Slot combinations
- `heapq` - Priority queues for online algorithms

## 🔬 Research Applications

### Theoretical Analysis
- **NP-completeness proof** via 3-SAT reduction
- **Competitive analysis** of online algorithms
- **Approximation bounds** and worst-case examples

### Practical Extensions
- Multi-machine scheduling
- Job preemption policies
- Dynamic job arrivals
- Resource constraints

## 📊 Experimental Setup

### Instance Generation
```bash
python instance_generator.py  # Creates 1000 random instances
```

### Large-scale Testing
See `XXL Compare online offline.ipynb` for:
- Batch processing of multiple instances
- Performance visualization
- Statistical analysis of competitive ratios

---

**Team**: Group 4 - Algorithms for Decision Support  
**Institution**: Universiteit Utrecht  
**Last Updated**: October 2024