from __future__ import annotations
from random import random, randint, shuffle, choices
import matplotlib.pyplot as plt


class Route:
    def __init__(self,name,capacity,college,dzone):
        self.name = name
        self.capacity = capacity
        self.college = college
        self.dzone = dzone

    def __repr__(self):
        return self.name


class Dzone:
    def __init__(self,name,location,radius,routes):
        self.name = name
        self.location = location
        self.radius = radius
        self.routes = routes

    def __repr__(self):
        return self.name


class College:
    def __init__(self, name:str, location:tuple, catchment_area:int, capacity:int, routes:list):
        self.name = name
        self.location = location
        self.catchment_area = catchment_area
        self.capacity = capacity
        self.routes = routes
        self.quality = random()
        self.priorities = []
        self.assigned_students:list[Student] = []

    def __repr__(self):
        return self.name
    
    def set_priorities(self, students:dict[str,Student], enable_routes=True):
        local_students = [
            s.name for s in students.values()
            if manhattan_distance(s.location,self.location) <= self.catchment_area
            ]
        non_local_students = [
            s.name for s in students.values()
            if s not in local_students
            ]
        routed_students = [
            (r,s.name) for s in students.values()
            for p in s.preferences
            if (r:=extract_route(p)) in self.routes
            and extract_college(p) == self.name
            ] if enable_routes else []

        high_priority = local_students + routed_students
        low_priority = non_local_students

        weights = {}
        for p in high_priority:
            s = extract_student(p)
            r = extract_route(p)
            if r: weights[p] = (
                1 / max(manhattan_distance(students[s].location,self.location), 1)
            )
            else: weights[p] = (
                1 / max(manhattan_distance(students[s].location,self.location), 1)
            )
        high_priority.sort(key=lambda p: weights[p], reverse=True)

        weights = {}
        for p in low_priority:
            s = extract_student(p)
            weights[p] = (
                1 / max(manhattan_distance(students[s].location,self.location), 1)
            )
        low_priority.sort(key=lambda p: weights[p], reverse=True)
        
        # shuffle(high_priority_students)
        # shuffle(non_local_students)

        self.priorities = high_priority + low_priority
        pass

    def assign_student(self, student):
        self.assigned_students.append(student)
        pass

    def unassign_student(self, student):
        self.assigned_students.remove(student)
        pass

    def show_diversity(self, students:dict[str,Student]):
        count = [students.get(extract_student(s)).SES for s in self.assigned_students]
        return sum(count)/len(count) if count else 0


class Student:
    def __init__(self, name:str, location:tuple):
        self.name = name
        self.location = location
        self.accesible_routes = []
        self.attended_dzones = []
        self.local_colleges = []
        self.preferences = []
        self.SES = randint(0,1)
        self.assigned_college = None
    

    def __repr__(self):
        return self.name
    
    
    def assign_college(self, college):
        """Assign a college to the student."""
        self.assigned_college = college
        pass


    def unassign_college(self):
        """Unassign the student's college."""
        self.assigned_college = None
        pass
    
    
    def set_location(self, grid_size, colleges:dict[str,College]):
        """Set the student's location depending on their SES."""
        # college = choice([c for c in colleges.values() if c.quality >= 0.8])
        # college = choice(
        #     sorted(
        #         colleges.values(),
        #         key=lambda c: getattr(c, 'quality'),
        #         reverse=True
        #     )[:int(0.3*len(colleges))]
        # )
        college = choices(
            population=[c for c in colleges.values()],
            weights=[c.quality**3 for c in colleges.values()]
        )[0]

        if self.SES and college:
            dx = randint(
                -college.catchment_area,
                college.catchment_area
            )
            dy = randint(
                -college.catchment_area-abs(dx),
                college.catchment_area-abs(dx)
            )
            self.location = (
                college.location[0]+dx,
                college.location[1]+dy
            )

        elif college:
            while manhattan_distance(self.location,college.location) <= college.catchment_area:
                self.location = generate_location(0,grid_size,0,grid_size)
        

    def set_locality_and_dzones(self, colleges:dict[str,College], dzones:dict[str,Dzone]):
        """Set the things"""
        for college in colleges.values():
            if manhattan_distance(self.location,college.location) <= college.catchment_area:
                self.local_colleges.append(college.name)
        for dzone in dzones.values():
            if manhattan_distance(self.location,dzone.location) <= dzone.radius:
                self.attended_dzones.append(dzone.name)
                self.accesible_routes.extend(dzone.routes)
                
    
    def set_preferences(self, colleges:dict[str,College],
                        enable_routes=True, enable_ties=False, enable_incomplete_lists=False):
        """Set the student's preferences over colleges and routes based on college quality, locality, and route access.

        Args:
            colleges (dict[str,College]): Dictionary of college objects.
            enable_routes (bool, optional): _description_. Defaults to True.
            enable_ties (bool, optional): _description_. Defaults to False.
            enable_incomplete_lists (bool, optional): _description_. Defaults to False.
        """
        self.preferences.extend([c.name for c in colleges.values()])
        for c in colleges.values():
            if c.routes and enable_routes:
                for r in c.routes:
                    if r in self.accesible_routes and c.name not in self.local_colleges:
                        self.preferences.append((r,c.name))

        weights = {}
        for p in self.preferences:
            c = extract_college(p)
            r = extract_route(p)
            if self.SES:
                weight = (
                    (0.9*colleges[c].quality + 0.1*random())
                    / max(manhattan_distance(self.location,colleges[c].location), 1)
                )
                if c in self.local_colleges: weight *= 2
                weights[p] = weight
            else:
                weight = (
                    (0.9*colleges[c].quality + 0.1*random())
                    / max(manhattan_distance(self.location,colleges[c].location), 1)
                )
                if c in self.local_colleges: weight *= 2
                if r: weight *= 5
                weights[p] = weight
        self.preferences.sort(key=lambda p: weights[p], reverse=True)
        if enable_incomplete_lists:
            self.preferences = self.preferences[:randint(1,len(self.preferences))]
        return weights


def manhattan_distance(start_coords,end_coords):
    return abs(start_coords[0]-end_coords[0]) + abs(start_coords[1]-end_coords[1])

def generate_location(x_min=0,x_max=0,y_min=0,y_max=0):
    return (randint(x_min,x_max), randint(y_min,y_max))

def dissimilarity_index(students:dict[str,Student], colleges:dict[str,College]):
    """Calculates the college's diversity index from student SES values."""
    L = len([student for student in students.values() if student.SES == 0])
    H = len(students)-L
    c_divs = [] #;print("L and H",L,H) # bugfixing print statement
    for k,v in colleges.items():
        h = l = 0
        for s in v.assigned_students:
            if students[extract_student(s)].SES == 1: h+=1
            else: l+=1
        c_divs.append(abs(h/H - l/L)) if L and H else c_divs.append(0)
    return 0.5*sum(c_divs)

def extract_route(matching_preference):
    """Extract route from preference."""
    if isinstance(matching_preference,tuple): return matching_preference[0]
    else: return None

def extract_college(matching_preference):
    """Extract college from preference."""
    if isinstance(matching_preference,tuple): return matching_preference[1]
    else: return matching_preference

def extract_student(assigned_object):
    """Extract student from assigned tuple."""
    if isinstance(assigned_object,tuple): return assigned_object[1]
    else: return assigned_object

def match_to_priority(student, preference):
    """Convert matching item to college priority."""
    if isinstance(preference, tuple):
        route = preference[0]
        return (route, student)
    else:
        return student

def college_oversubscription(
        students:dict[str,Student], colleges:dict[str,College],
        free:list[str], matching:dict, unassigned:list[str],
        college_priorities:dict, c:str,
        verbose=False
):
    """Run if current college capacity reaches 0."""
    if verbose: print(f"{c} has reached capacity!")
    if verbose: print(f"current priority list for {c}: {colleges[c].priorities}")

    # create ranking of currently assigned students according to college priorities
    ranking = {priority:rank for rank,priority in enumerate(college_priorities[c])}
    lowest_priority = max((student for student in colleges[c].assigned_students),
                        key=lambda student: ranking[student], default=None)
    
    if verbose: print(f"lowest priority in the matching for {c} is {lowest_priority}")
    
    # unmatch lowest priority student and update their preference list, the college's priority list and assigned students, and the free and unassigned lists
    lowest_priority_student = extract_student(lowest_priority)
    students[lowest_priority_student].unassign_college()
    if verbose: print(f"{lowest_priority_student} unmatched with {matching[lowest_priority_student]}")

    students[lowest_priority_student].preferences.remove(matching[lowest_priority_student])
    if verbose: print(f"reduced preference list for {lowest_priority_student}: {students[lowest_priority_student].preferences}")

    colleges[c].priorities.remove(lowest_priority)
    if verbose: print(f"reduced priority list for {c}: {colleges[c].priorities}")

    colleges[c].unassign_student(lowest_priority)
    if verbose: print(f"reduced assignments to {c}: {colleges[c].assigned_students}")

    matching.pop(lowest_priority_student)

    if students[lowest_priority_student].preferences:
        free.append(lowest_priority_student)
    else:
        unassigned.append(lowest_priority_student)
        if verbose: print(f"{lowest_priority_student} has emptied their preference list and is unassigned")
    
    if verbose: print("new list of free students:",free)

def route_oversubscription(
        students:dict[str,Student], colleges:dict[str,College],
        free:list, matching:dict, unassigned:list,
        s:str, c:str, r:str,
        verbose=False
):
    """Run if current route capacity reaches 0."""
    if verbose: print(f"{r} has reached capacity!", f"{r} serves {c}", f"current priority list for {c}: {colleges[c].priorities}", sep="\n")

    ranking = {priority:rank for rank,priority in enumerate([p for p in colleges[c].priorities if isinstance(p,tuple) and r in p])}
    lowest_priority = max((student for student,preference in matching.items() if match_to_priority(student,preference) in ranking),
                        key=lambda student: ranking[match_to_priority(student,matching[student])], default=None)
    
    students[lowest_priority].unassign_college()
    if verbose: print(f"lowest priority routed student assigned to {c} is {lowest_priority}")
    if verbose: print(f"{lowest_priority} unmatched with {matching[lowest_priority]}")

    students[lowest_priority].preferences.remove(matching[lowest_priority])
    if verbose: print(f"reduced preference list for {lowest_priority}: {students[lowest_priority].preferences}")

    colleges[c].priorities.remove((r,lowest_priority))
    if verbose: print(f"reduced priority list for {c}: {colleges[c].priorities}")

    colleges[c].unassign_student((r,lowest_priority))
    if verbose: print(f"reduced assignments to {c}: {colleges[c].assigned_students}")

    matching.pop(lowest_priority)

    if students[lowest_priority].preferences:
        free.append(lowest_priority)
    else:
        unassigned.append(lowest_priority)
        if verbose: print(f"{lowest_priority} has emptied their preference list and is unassigned")
    
    if verbose: print("new list of free students:",free)

def greedy_matching(student_names:list, students:dict[str,Student], colleges:dict[str,College], routes:dict[str,Route], verbose=False):
    """Greedy matching algorithm"""
    free = student_names.copy()
    shuffle(free)
    matching = {}
    unassigned = []

    while free:
        print(free) if verbose else None

        # pop the first student in the list
        s = free.pop(0)

        # handle empty preference lists
        if not students[s].preferences:
            unassigned.append(s)
            print(f"student {s} has emptied their preference list and is unassigned", "-"*50, sep="\n") if verbose else None
            continue

        # pop the top college on s's preference list and handle empty preference lists
        p = students[s].preferences.pop(0)

        #handle oversubscription
        r = extract_route(p)
        c = extract_college(p)

        if r:
            if routes[r].capacity and colleges[c].capacity:
                matching.update({s:p})
                students[s].assign_college(c)
                colleges[c].assign_student(match_to_priority(s,p))
                routes[r].capacity -= 1 ;colleges[c].capacity -= 1
            elif routes[r].capacity and not colleges[c].capacity:
                print("COLLEGE CAPACITY") if verbose else None
                free.append(s)
                continue
            else:
                print("ROUTE CAPACITY") if verbose else None
                free.append(s)
                continue
        
        else:
            if colleges[c].capacity:
                matching.update({s:p})
                students[s].assign_college(c)
                colleges[c].assign_student(match_to_priority(s,p))
                colleges[c].capacity -= 1
            else:
                print("COLLEGE CAPACITY") if verbose else None
                free.append(s)
                continue
    
    di = dissimilarity_index(students, colleges)
    print(di) if verbose else None

    print("END") if verbose else None

    return students, colleges, routes, matching, unassigned, di

def routed_acceptance(
        student_names:list[str], college_priorities:dict[str,list],
        students:dict[str,Student], colleges:dict[str,College], routes:dict[str,Route],
        verbose=False
):
    """Modified Deferred Accepance algorithm."""

    free = student_names.copy()
    matching = {}
    unassigned = []
    n_proposals = 0

    print(f"\n{"-"*50}\nBEGIN MATCHING\n{"-"*50}\n") if verbose else None

    while free:
        # Display remaining free students and available college/route capacity
        print(f"list of free students:\n {free}", "-"*50,
              *[f"remaining {c} capacity is {c.capacity}" for c in colleges.values()], "-"*50,
              *[f"remaining {r} capacity is {r.capacity}" for r in routes.values()], "-"*50,
              sep="\n") if verbose else None

        # assign first student in the list of free students
        s = free.pop(0) # argument selects the first student in the list
        print(f"assigning student {s}",
              f"{s} has preferences:\n {students[s].preferences}" if students[s].preferences else f"{s} has emptied their preference list",
              sep="\n") if verbose else None

        # handle empty preference lists
        if not students[s].preferences:
            unassigned.append(s)
            print(f"student {s} has emptied their preference list and is unassigned",
                  "-"*50, sep="\n") if verbose else None
            continue

        # Update the number of proposals
        n_proposals += 1

        # identify first student's top preference
        p = students[s].preferences[0]
        print(f"{s}'s top preference is {p}", "-"*50, sep="\n") if verbose else None

        # extract route and college from s's top preference
        r = extract_route(p)
        c = extract_college(p)

        # tentative matching
        matching.update({s:p})
        print(f"tentative matching:\n {matching}", "-"*50, sep="\n") if verbose else None

        # update assigned students and colleges
        colleges[c].assign_student(match_to_priority(s,p))
        students[s].assign_college(p)
        print("assigned students:", *[f" {x}, {y.assigned_students}" for x,y in colleges.items()], "-"*50, sep="\n") if verbose else None

        # handle oversubscription
        if r:
            if routes[r].capacity and colleges[c].capacity:
                routes[r].capacity -= 1; colleges[c].capacity -= 1
                continue
            elif routes[r].capacity and not colleges[c].capacity:
                college_oversubscription(students,colleges,free,matching,unassigned,college_priorities,c)
                continue
            else:
                route_oversubscription(students,colleges,free,matching,unassigned,s,c,r)
                continue
        else:
            if colleges[c].capacity:
                colleges[c].capacity -= 1
                continue
            else:
                college_oversubscription(students,colleges,free,matching,unassigned,college_priorities,c)
                continue

    print(f"final number of proposals: {n_proposals}",
          f"maximum number of proposals: {len(students)*len(colleges)}",
          f"ratio: {100*n_proposals/(len(students)*len(colleges))}",
          sep="\n") if verbose else None
    print(f"\n{"-"*50}\nEND MATCHING\n{"-"*50}\n") if verbose else None

    di = dissimilarity_index(students, colleges)

    return students, colleges, routes, matching, unassigned, di

def check_stability(
        student_preferences:dict[str,list], college_priorities:dict[str,list],
        colleges:dict[str,College], routes:dict[str,Route],
        matching, unassigned, verbose=False):
    """Checks the stability of the matching."""
    if verbose: print(f"\n{"-"*50}\nCHECKING MATCHED STUDENTS\n{"-"*50}\n")
    blocking_pairs = []
    for s,mp in matching.items():
        if verbose: print(f"\nstudent {s} has preferences {student_preferences[s]} and was matched to {mp}\n")
        for p in student_preferences[s]:
            if p is mp: break
            else: # p in matching.values():
                c = extract_college(p)
                r = extract_route(p)
                spr = match_to_priority(s,p)
                assigned_student_priority_indices = [college_priorities[c].index(i) for i in colleges[c].assigned_students]
                if colleges[c].capacity and r:
                    if routes[r].capacity: blocking_pairs.append((s,p)) ;print(f"blocking pair found: {s,p}") if verbose else None
                    else: print(f"{c} has spare capacity but {r}'s route capacity reached so {spr} was rejected during matching so\nno blocking pairs\n") if verbose else None
                elif colleges[c].capacity:
                    blocking_pairs.append((s,p)) ;print(f"college {c} has spare capacity so blocking pair found: {s,p}\n") if verbose else None
                    continue
                if verbose: print(
                    f"{s} not matched to top choice!\n",
                    f"college {c} from preference {p} has priorities {college_priorities[c]}\n",
                    f"and was assigned: {colleges[c].assigned_students}\n",
                    f"{c}'s assigned student priority indices: {assigned_student_priority_indices}\n",
                    f"{spr}'s priority index: {college_priorities[c].index(spr)}\n"
                    )
                #print(f"{college_priorities[c].index(match_to_priority(s,mp))} {assigned_student_priority_indices}")
                if college_priorities[c].index(spr) <= max(assigned_student_priority_indices): 
                    if r:
                        if routes[r].capacity: blocking_pairs.append((s,p)) ;print(f"blocking pair found: {s,p}") if verbose else None
                        else: print(f"{r}'s route capacity reached so {spr} was rejected during matching so\nno blocking pairs\n") if verbose else None
                    else: print(f"{s}'s routed preferences have reached route capacity so {spr} rejected\nno blocking pairs\n") if verbose else None
                else: print("no blocking pairs\n") if verbose else None

    if verbose: print(f"\n{"-"*50}\nCHECKING UNASSIGNED STUDENTS\n{"-"*50}\n")
    for s in unassigned:
        if verbose: print(f"\nstudent {s} has preferences: {student_preferences[s]}\n")
        for p in student_preferences[s]:
            if verbose: print(f"checking preference {p}:")
            if p in matching.values():
                c = extract_college(p)
                r = extract_route(p)
                spr = match_to_priority(s,p)
                assigned_student_priority_indices = [college_priorities[c].index(i) for i in colleges[c].assigned_students]
                if colleges[c].capacity and r:
                    if routes[r].capacity: blocking_pairs.append((s,p)) ;print(f"blocking pair found: {s,p}") if verbose else None
                    else: print(f"{c} has spare capacity but {r}'s route capacity reached so {spr} was rejected during matching so\nno blocking pairs\n") if verbose else None
                elif colleges[c].capacity:
                    blocking_pairs.append((s,p)) ;print(f"college {c} has spare capacity so blocking pair found: {s,p}\n") if verbose else None
                    continue
                if verbose: print(
                    f"{c} is already matched!\n",
                    f"{c} has priorities: {college_priorities[c]}\n",
                    f"and was assigned: {colleges[c].assigned_students}\n",
                    f"{c}'s assigned student priority indices: {assigned_student_priority_indices}\n",
                    f"{spr}'s priority index: {college_priorities[c].index(spr)}\n"
                    )
                if max(assigned_student_priority_indices) >= college_priorities[c].index(spr):
                    if r:
                        if routes[r].capacity: blocking_pairs.append((s,p)) ;print(f"blocking pair found: {s,p}\n") if verbose else None
                        else: print(f"{r}'s route capacity reached so {spr} was rejected during matching so\nno blocking pairs\n") if verbose else None
                    else: print(f"{s}'s routed preferences have reached route capacity so {spr} rejected\nno blocking pairs\n") if verbose else None
                else: print(f"no blocking pairs\n") if verbose else None
    return blocking_pairs

def compare_Pareto_performance(student_names:list, student_preferences:dict, matching_1:dict, matching_2:dict):
    if set(matching_1) != set(matching_2): raise ValueError("Matchings must contain the same agents.")
    one_better = False

    for student in matching_1.keys():
        match_1 = extract_college(matching_1[student])
        match_2 = extract_college(matching_2[student])

        pos_1 = student_preferences[student].index(match_1) #if match_1 else 0
        pos_2 = student_preferences[student].index(match_2) #if match_2 else 0

        if pos_1 < pos_2: return False
        elif pos_1 > pos_2: one_better = True
        pass
    return one_better

def compare_college_quality(students_1:dict[str,Student], students_2:dict[str,Student],
                            colleges_1:dict[str,College], colleges_2:dict[str,College],
                            matching_1:dict, matching_2:dict, student_names:list):
    """
    Compare the average quality of colleges assigned to students in two matchings.
    """

    if set(matching_1) != set(matching_2): raise ValueError("Matchings must contain the same agents.")

    quality_comparison = {}
    for s,p in matching_1.items():
        if colleges_1.get(p).quality > colleges_2.get(matching_2.get(s)).quality:
            quality_comparison[s] = 1
        else:
            quality_comparison[s] = 0
        pass
    return quality_comparison, sum(quality_comparison.values())/len(quality_comparison) if quality_comparison else 0

def visualize(students:dict[str,Student], colleges:dict[str,College], dzones:dict[str,Dzone], grid_size, n_cols=1, plot_number=0):
    """Visualize locations of students, colleges, and disadvantaged zones."""
    fig, ax = plt.subplots(ncols=n_cols, figsize=(10*n_cols, 10))
    
    # Plot assignment lines first (so they appear behind points)
    for s in students.values():
        if hasattr(s, 'assigned_college') and s.assigned_college:
            c = extract_college(s.assigned_college)
            r = extract_route(s.assigned_college)
            if r: color = "green"; alpha = 0.6
            # elif c in s.local_colleges and s.SES: color = "purple"; alpha = 0.6
            # elif c in s.local_colleges: color = "brown"; alpha = 0.6
            elif s.SES: color = "blue"; alpha = 0.3
            elif not s.SES: color = "red"; alpha = 0.3
            if n_cols == 1: ax.plot(
                [s.location[0], colleges[c].location[0]],
                [s.location[1], colleges[c].location[1]],
                color=color, alpha=alpha, linewidth=1
            )
            else: ax[plot_number].plot(
                [s.location[0], colleges[c].location[0]],
                [s.location[1], colleges[c].location[1]],
                color=color, alpha=alpha, linewidth=1
            )
    
    # Plot students
    rich_student_locs = [s.location for s in students.values() if s.SES]
    ax.scatter(*zip(*rich_student_locs), c='purple', s=30, alpha=0.6, label='High-type students', zorder=3)
    poor_student_locs = [s.location for s in students.values() if not s.SES]
    ax.scatter(*zip(*poor_student_locs), c='green', s=30, alpha=0.6, label='Low-type students', zorder=3)
    
    # Plot colleges with catchment areas (Manhattan distance = diamond shape)
    for c in colleges.values():
        ax.scatter(*c.location, c='red', s=300, marker='s',
                  edgecolors='black', linewidths=2, zorder=4,
                  label='School' if c == list(colleges.values())[0] else '')
        # Manhattan distance creates a diamond/square rotated 45 degrees
        x, y = c.location
        r = c.catchment_area
        diamond = plt.Polygon([(x+r, y), (x, y+r), (x-r, y), (x, y-r)], 
                             fill=False, edgecolor='red', linestyle='--', alpha=0.6)
        ax.add_patch(diamond)
        ax.text(x, y, f"{c.name}\n{c.quality:.2g}", ha='center', va='center', fontsize=8, zorder=5)
    
    # Plot dzones (Manhattan distance = diamond shape)
    for d in dzones.values():
        x, y = d.location
        r = d.radius
        diamond = plt.Polygon([(x+r, y), (x, y+r), (x-r, y), (x, y-r)], 
                             fill=True, facecolor='orange', alpha=0.6, 
                             edgecolor='orange', linewidth=2,
                             label='Disadvantaged zone' if d == list(dzones.values())[0] else '')
        ax.add_patch(diamond)
        ax.scatter(x, y, c='orange', s=100, marker='^', edgecolors='black', zorder=3)
    
    ax.set_xlim(0, grid_size)
    ax.set_ylim(0, grid_size)
    ax.set_aspect('equal')
    ax.legend()
    # ax.set_title('Student Assignment Simulation Map')
    ax.set_xlabel('X coordinate')
    ax.set_ylabel('Y coordinate')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig