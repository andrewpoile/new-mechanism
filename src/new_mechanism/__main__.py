from random import seed, randint
from .utils import Student, College, Dzone, Route, manhattan_distance, generate_location


def initialise_randomly(random_seed, grid_size=1000,
        student_names = None, college_names = None, route_names = None, dzone_names = None,
        n_students=200, n_colleges=10, n_routes=30, n_dzones=3, c_cap=2, r_cap=1, class_size=30,
        min_students=10, min_colleges=2, min_dzones=3, min_routes=1.0,
        max_students=20, max_colleges=8, max_dzones=3, max_routes=1.0,
        min_college_capacity=0.75, max_college_capacity=1.25,
        min_route_capacity=0.25, max_route_capacity=1.00,
        min_catchment_area=0.2, max_catchment_area=0.2,
        min_dzone_radius=0.1, max_dzone_radius=0.1,
        verbose=False, restricted=False, shuffle_student_preferences=True,
        enable_routes=True, enable_ties=False, enable_incomplete_lists=False
):
    """Function to initialise all students and colleges randomly with routes and local students."""
    # Set random seed
    seed(random_seed)

    # Set number, size and location of disadvantaged zones
    # n_dzones = randint(min_dzones,max_dzones) if randomised else n_dzones
    # d_zones = []
    # for i in range(n_dzones):
    #     dzone_coords = (randint(0,grid_size),randint(0,grid_size)) if randomised else (int(grid_size*i/10),int(grid_size*i/10))
    #     dzone_radius = randint(int(min_dzone_radius*grid_size), int(max_dzone_radius*grid_size)) if randomised else int(0.1*grid_size)
    #     d_zones.append((dzone_coords,dzone_radius))

    # Randomly generated number of participants, routes and dzones
    n_students = randint(
        min_students,max_students
        ) if not student_names else n_students
    
    n_colleges = randint(
        min_colleges,max_colleges
        ) if not college_names else n_colleges
    
    n_dzones = randint(
        min_dzones,max_dzones
        ) if not dzone_names else n_dzones
    
    n_routes = randint(
        int(min_routes*n_colleges*n_dzones),
        int(max_routes*n_colleges*n_dzones)
        ) if not route_names else n_colleges*n_dzones

    # Lists of all participants, routes, and dzones
    if not student_names: student_names = [f"s_{i+1}" for i in range(n_students)]
    if not college_names: college_names = [f"c_{i+1}" for i in range(n_colleges)]
    if not dzone_names: dzone_names = [f"dz_{i+1}" for i in range(n_dzones)]
    if not route_names: route_names = [f"r_{i+1}" for i in range(n_routes)]
    print(f"list of student names: {student_names}",
          f"list of college names: {college_names}",
          f"list of dzone names: {dzone_names}",
          f"list of route names: {route_names}",
          "-"*50, sep="\n") if verbose else None

    # Capacities of colleges and routes
    c_caps = {c:randint(
        max(
            class_size,
            class_size*int((min_college_capacity*n_students)/(n_colleges*class_size))
            ),
        max(
            class_size,
            class_size*int((max_college_capacity*n_students)/(n_colleges*class_size))
            )
        ) for c in college_names
    } if not college_names else {c:c_cap for c in college_names}

    r_caps = {r:randint(
        max(30,30*int((min_route_capacity*n_students)/(n_colleges*30))),
        max(30,30*int((max_route_capacity*n_students)/(n_colleges*30)))
        ) for r in route_names
    } if not route_names else {r:r_cap for r in route_names}

    print(f"college capacities:",*[f"{k}: {v}" for k,v in c_caps.items()],
          f"route capacities:",*[f"{k}: {v}" for k,v in r_caps.items()],
          "-"*50, sep="\n") if verbose else None
    
    # Route services
    college_routes = {
        college:route_names[i*n_dzones:(i+1)*n_dzones if i*n_dzones < n_routes else None]
        for i,college in enumerate(college_names)
    }
    # college_routes = {
    #     college: (route_names[i*n_dzones:(i+1)*n_dzones] + [None] * n_dzones)[:n_dzones]
    #     for i, college in enumerate(college_names)
    # }
    
    dzone_routes = {
        dzone:[college_routes[c][i] for c in college_names if i < len(college_routes[c])]
        for i,dzone in enumerate(dzone_names)
    }
    # dzone_routes = {
    #     dzone:[college_routes[c][i] for c in college_names if college_routes[c][i]]
    #     for i,dzone in enumerate(dzone_names)
    # }
    
    # Assign class objects
    students = {
        s:Student(
            s,
            generate_location(0,grid_size,0,grid_size)
        ) for s in student_names
    }

    # Assign college location ensuring no co-location
    college_locations = dict()
    for c in college_names:
        location = generate_location(0,grid_size,0,grid_size)
        while location in college_locations.values():
            location = generate_location(0,grid_size,0,grid_size)
        college_locations[c] = location
        pass

    colleges = {
        c:College(
            c,
            college_locations[c],
            randint(
                int(min_catchment_area*grid_size),
                int(max_catchment_area*grid_size)
                ),
            c_caps[c],
            college_routes[c]
        ) for c in college_names
    }

    # Assign dzone location ensuring no co-location or overlap with high quality college catchment areas
    dzone_locations = dict()
    for d in dzone_names:
        location = generate_location(0,grid_size,0,grid_size)
        while location in dzone_locations.values() or any(
            manhattan_distance(location,college.location)
            <= college.catchment_area + int(max_dzone_radius*grid_size)
            for college in colleges.values()
            if college.quality >= 0.5
        ):
            location = generate_location(0,grid_size,0,grid_size)
        dzone_locations[d] = location
        pass

    dzones = {
        d:Dzone(
            d,
            dzone_locations[d],
            randint(
                int(min_dzone_radius*grid_size),
                int(max_dzone_radius*grid_size)
                ),
            dzone_routes[d]
        ) for d in dzone_names
    }

    routes = {
        r:Route(
            r,
            r_caps[r],
            [c for c in college_names if r in colleges[c].routes],
            [dz for dz in dzone_names if r in dzones[dz].routes]
        ) for r in route_names
    }

    for s in student_names:
        students[s].set_location(grid_size, colleges)
        pass

    for s in student_names:
        students[s].set_locality_and_dzones(colleges, dzones)
        students[s].set_preferences(
            colleges,
            enable_routes=enable_routes,
            enable_ties=enable_ties,
            enable_incomplete_lists=enable_incomplete_lists
            )
        pass
    
    for c in college_names:
        colleges[c].set_priorities(students, enable_routes=enable_routes)
        pass

    student_preferences = {s:students[s].preferences[:] for s in student_names}
    college_priorities = {c:colleges[c].priorities[:] for c in college_names}

    return student_names, college_names, route_names, student_preferences, college_priorities, students, colleges, dzones, routes


def initialise_withdata(
        student_names, college_names, route_names, dzone_names
):
    n_students = len(student_names)
    n_colleges = len(college_names)
    n_routes = len(route_names)
    n_dzones = len(dzone_names)
    pass