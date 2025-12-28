<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  interface Resource {
    id: string;
    name: string;
    email: string;
    role: string;
    department: string;
    skills: string[];
    availability: number; // 0-100 percentage
    currentProjects: string[];
    capacity: number; // hours per week
    utilization: number; // percentage
    avatar?: string;
  }
  
  interface Project {
    id: string;
    name: string;
    priority: 'high' | 'medium' | 'low';
    deadline: string;
    resourceNeeds: ResourceNeed[];
  }
  
  interface ResourceNeed {
    skill: string;
    hours: number;
    assigned?: string; // resource ID
  }
  
  interface Allocation {
    id: string;
    resourceId: string;
    projectId: string;
    hours: number;
    startDate: string;
    endDate: string;
    role: string;
  }
  
  let resources = writable<Resource[]>([]);
  let projects = writable<Project[]>([]);
  let allocations = writable<Allocation[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- used in template
  let selectedResource: Resource | null = null;
  let selectedView: 'grid' | 'timeline' | 'utilization' = 'grid';
  let filterDepartment = 'all';
  let filterSkill = '';
  let showUnderUtilized = false;
  let showOverAllocated = false;
  
  onMount(async () => {
    await loadResources();
    await loadProjects();
    await loadAllocations();
  });
  
  async function loadResources() {
    // Mock data for resources
    resources.set([
      {
        id: 'r1',
        name: 'Alice Chen',
        email: 'alice@convergio.com',
        role: 'Senior Developer',
        department: 'Engineering',
        skills: ['Python', 'React', 'AWS', 'Machine Learning'],
        availability: 100,
        currentProjects: ['p1', 'p2'],
        capacity: 40,
        utilization: 85,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alice'
      },
      {
        id: 'r2',
        name: 'Bob Martinez',
        email: 'bob@convergio.com',
        role: 'UX Designer',
        department: 'Design',
        skills: ['Figma', 'User Research', 'Prototyping', 'Design Systems'],
        availability: 80,
        currentProjects: ['p1'],
        capacity: 40,
        utilization: 60,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob'
      },
      {
        id: 'r3',
        name: 'Carol Wang',
        email: 'carol@convergio.com',
        role: 'Product Manager',
        department: 'Product',
        skills: ['Agile', 'Strategy', 'Analytics', 'Roadmapping'],
        availability: 100,
        currentProjects: ['p1', 'p2', 'p3'],
        capacity: 40,
        utilization: 95,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Carol'
      },
      {
        id: 'r4',
        name: 'David Kumar',
        email: 'david@convergio.com',
        role: 'DevOps Engineer',
        department: 'Engineering',
        skills: ['Kubernetes', 'Docker', 'CI/CD', 'Terraform'],
        availability: 100,
        currentProjects: ['p2'],
        capacity: 40,
        utilization: 45,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=David'
      }
    ]);
  }
  
  async function loadProjects() {
    // Mock data for projects
    projects.set([
      {
        id: 'p1',
        name: 'AI Platform Development',
        priority: 'high',
        deadline: '2025-09-30',
        resourceNeeds: [
          { skill: 'Python', hours: 20, assigned: 'r1' },
          { skill: 'React', hours: 15, assigned: 'r1' },
          { skill: 'UX Design', hours: 10, assigned: 'r2' }
        ]
      },
      {
        id: 'p2',
        name: 'Mobile App Launch',
        priority: 'medium',
        deadline: '2025-10-15',
        resourceNeeds: [
          { skill: 'React Native', hours: 25 },
          { skill: 'DevOps', hours: 10, assigned: 'r4' }
        ]
      },
      {
        id: 'p3',
        name: 'Customer Portal Redesign',
        priority: 'medium',
        deadline: '2025-11-01',
        resourceNeeds: [
          { skill: 'Figma', hours: 20 },
          { skill: 'User Research', hours: 15 }
        ]
      }
    ]);
  }
  
  async function loadAllocations() {
    // Mock data for allocations
    allocations.set([
      {
        id: 'a1',
        resourceId: 'r1',
        projectId: 'p1',
        hours: 20,
        startDate: '2025-08-15',
        endDate: '2025-09-30',
        role: 'Lead Developer'
      },
      {
        id: 'a2',
        resourceId: 'r2',
        projectId: 'p1',
        hours: 10,
        startDate: '2025-08-15',
        endDate: '2025-09-15',
        role: 'UX Designer'
      },
      {
        id: 'a3',
        resourceId: 'r3',
        projectId: 'p1',
        hours: 15,
        startDate: '2025-08-15',
        endDate: '2025-09-30',
        role: 'Product Manager'
      }
    ]);
  }
  
  function getUtilizationColor(utilization: number): string {
    if (utilization >= 90) return 'text-red-600 bg-red-50';
    if (utilization >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  }
  
  function getAvailabilityColor(availability: number): string {
    if (availability === 100) return 'bg-green-500';
    if (availability >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  }
  
  function getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-surface-600 bg-surface-50';
    }
  }
  
  function assignResource(_resourceId: string, _projectId: string, _skill: string) {
    // Logic to assign resource to project
  }
  
  $: filteredResources = $resources.filter(resource => {
    const matchesDepartment = filterDepartment === 'all' || resource.department === filterDepartment;
    const matchesSkill = !filterSkill || resource.skills.some(s => 
      s.toLowerCase().includes(filterSkill.toLowerCase())
    );
    const matchesUtilization = (!showUnderUtilized || resource.utilization < 50) &&
                               (!showOverAllocated || resource.utilization > 90);
    return matchesDepartment && matchesSkill && matchesUtilization;
  });
  
  $: departments = [...new Set($resources.map(r => r.department))];
</script>

<div class="resource-board p-6">
  <!-- Header -->
  <div class="mb-6">
    <h2 class="text-2xl font-bold text-surface-900">Resource Management</h2>
    <p class="text-surface-600">Manage team allocation and capacity</p>
  </div>
  
  <!-- View Selector and Filters -->
  <div class="bg-white rounded-lg shadow p-4 mb-6">
    <div class="flex flex-wrap gap-4 items-center">
      <!-- View Selector -->
      <div class="flex gap-2">
        <button
          on:click={() => selectedView = 'grid'}
          class="px-3 py-2 rounded {selectedView === 'grid' ? 'bg-blue-600 text-white' : 'bg-surface-100'}"
        >
          Grid View
        </button>
        <button
          on:click={() => selectedView = 'timeline'}
          class="px-3 py-2 rounded {selectedView === 'timeline' ? 'bg-blue-600 text-white' : 'bg-surface-100'}"
        >
          Timeline
        </button>
        <button
          on:click={() => selectedView = 'utilization'}
          class="px-3 py-2 rounded {selectedView === 'utilization' ? 'bg-blue-600 text-white' : 'bg-surface-100'}"
        >
          Utilization
        </button>
      </div>
      
      <!-- Filters -->
      <select
        bind:value={filterDepartment}
        class="px-3 py-2 border rounded-lg"
      >
        <option value="all">All Departments</option>
        {#each departments as dept}
          <option value={dept}>{dept}</option>
        {/each}
      </select>
      
      <input
        type="text"
        placeholder="Filter by skill..."
        bind:value={filterSkill}
        class="px-3 py-2 border rounded-lg"
      />
      
      <label class="flex items-center gap-2">
        <input type="checkbox" bind:checked={showUnderUtilized} />
        <span>Under-utilized</span>
      </label>
      
      <label class="flex items-center gap-2">
        <input type="checkbox" bind:checked={showOverAllocated} />
        <span>Over-allocated</span>
      </label>
    </div>
  </div>
  
  <!-- Grid View -->
  {#if selectedView === 'grid'}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {#each filteredResources as resource}
        <div class="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
          <!-- Resource Header -->
          <div class="flex items-start gap-3 mb-3">
            <img
              src={resource.avatar}
              alt={resource.name}
              class="w-12 h-12 rounded-full"
            />
            <div class="flex-1">
              <h3 class="font-semibold">{resource.name}</h3>
              <p class="text-sm text-surface-600">{resource.role}</p>
              <p class="text-xs text-surface-500">{resource.department}</p>
            </div>
          </div>
          
          <!-- Availability Bar -->
          <div class="mb-3">
            <div class="flex justify-between text-xs mb-1">
              <span>Availability</span>
              <span>{resource.availability}%</span>
            </div>
            <div class="w-full bg-surface-200 rounded-full h-2">
              <div
                class="h-2 rounded-full {getAvailabilityColor(resource.availability)}"
                style="width: {resource.availability}%"
              ></div>
            </div>
          </div>
          
          <!-- Utilization -->
          <div class="mb-3">
            <span class="px-2 py-1 text-xs font-medium rounded-full {getUtilizationColor(resource.utilization)}">
              {resource.utilization}% Utilized
            </span>
          </div>
          
          <!-- Skills -->
          <div class="mb-3">
            <p class="text-xs font-medium text-surface-600 mb-1">Skills:</p>
            <div class="flex flex-wrap gap-1">
              {#each resource.skills.slice(0, 3) as skill}
                <span class="px-2 py-1 text-xs bg-surface-100 rounded">
                  {skill}
                </span>
              {/each}
              {#if resource.skills.length > 3}
                <span class="px-2 py-1 text-xs bg-surface-100 rounded">
                  +{resource.skills.length - 3}
                </span>
              {/if}
            </div>
          </div>
          
          <!-- Current Projects -->
          <div class="mb-3">
            <p class="text-xs font-medium text-surface-600 mb-1">
              Projects ({resource.currentProjects.length}):
            </p>
            <div class="space-y-1">
              {#each $projects.filter(p => resource.currentProjects.includes(p.id)).slice(0, 2) as project}
                <div class="text-xs text-surface-600">• {project.name}</div>
              {/each}
            </div>
          </div>
          
          <!-- Actions -->
          <button
            on:click={() => selectedResource = resource}
            class="w-full px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            View Details
          </button>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- Timeline View -->
  {#if selectedView === 'timeline'}
    <div class="bg-white rounded-lg shadow p-6">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b">
              <th class="text-left py-2 px-4">Resource</th>
              <th class="text-left py-2 px-4">Current Week</th>
              <th class="text-left py-2 px-4">Next Week</th>
              <th class="text-left py-2 px-4">Week 3</th>
              <th class="text-left py-2 px-4">Week 4</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredResources as resource}
              <tr class="border-b hover:bg-surface-50">
                <td class="py-3 px-4">
                  <div class="flex items-center gap-2">
                    <img
                      src={resource.avatar}
                      alt={resource.name}
                      class="w-8 h-8 rounded-full"
                    />
                    <div>
                      <div class="font-medium">{resource.name}</div>
                      <div class="text-xs text-surface-500">{resource.role}</div>
                    </div>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <div class="h-8 bg-blue-200 rounded flex items-center px-2 text-xs">
                    Project A (20h)
                  </div>
                </td>
                <td class="py-3 px-4">
                  <div class="h-8 bg-green-200 rounded flex items-center px-2 text-xs">
                    Project B (15h)
                  </div>
                </td>
                <td class="py-3 px-4">
                  <div class="h-8 bg-purple-200 rounded flex items-center px-2 text-xs">
                    Project C (25h)
                  </div>
                </td>
                <td class="py-3 px-4">
                  <div class="h-8 bg-surface-100 rounded flex items-center px-2 text-xs">
                    Available
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
  
  <!-- Utilization View -->
  {#if selectedView === 'utilization'}
    <div class="bg-white rounded-lg shadow p-6">
      <div class="space-y-4">
        {#each filteredResources as resource}
          <div class="flex items-center gap-4">
            <div class="w-48">
              <div class="flex items-center gap-2">
                <img
                  src={resource.avatar}
                  alt={resource.name}
                  class="w-8 h-8 rounded-full"
                />
                <div>
                  <div class="font-medium">{resource.name}</div>
                  <div class="text-xs text-surface-500">{resource.capacity}h/week</div>
                </div>
              </div>
            </div>
            
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-surface-200 rounded-full h-6">
                  <div
                    class="h-6 rounded-full flex items-center justify-center text-xs text-white
                           {resource.utilization >= 90 ? 'bg-red-500' : 
                            resource.utilization >= 70 ? 'bg-yellow-500' : 'bg-green-500'}"
                    style="width: {Math.min(100, resource.utilization)}%"
                  >
                    {resource.utilization}%
                  </div>
                </div>
                <span class="text-sm text-surface-600 w-20">
                  {Math.round(resource.capacity * resource.utilization / 100)}h used
                </span>
              </div>
            </div>
          </div>
        {/each}
      </div>
      
      <!-- Summary Stats -->
      <div class="mt-6 pt-6 border-t grid grid-cols-3 gap-4">
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">
            {$resources.filter(r => r.utilization < 70).length}
          </div>
          <div class="text-sm text-surface-600">Available</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-yellow-600">
            {$resources.filter(r => r.utilization >= 70 && r.utilization < 90).length}
          </div>
          <div class="text-sm text-surface-600">Allocated</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-red-600">
            {$resources.filter(r => r.utilization >= 90).length}
          </div>
          <div class="text-sm text-surface-600">Over-allocated</div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Unassigned Tasks Panel -->
  <div class="mt-6 bg-white rounded-lg shadow p-6">
    <h3 class="text-lg font-semibold mb-4">Unassigned Resource Needs</h3>
    <div class="space-y-3">
      {#each $projects as project}
        {#each project.resourceNeeds.filter(n => !n.assigned) as need}
          <div class="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
            <div>
              <span class="font-medium">{project.name}</span>
              <span class="px-2 py-1 ml-2 text-xs rounded-full {getPriorityColor(project.priority)}">
                {project.priority}
              </span>
              <div class="text-sm text-surface-600 mt-1">
                Needs: {need.skill} ({need.hours}h)
              </div>
            </div>
            <select
              on:change={(e) => {
                const target = e.target as HTMLSelectElement;
                if (target?.value) {
                  assignResource(target.value, project.id, need.skill);
                }
              }}
              class="px-3 py-2 border rounded-lg"
            >
              <option value="">Assign to...</option>
              {#each $resources.filter(r => r.skills.includes(need.skill)) as resource}
                <option value={resource.id}>
                  {resource.name} ({resource.availability}% available)
                </option>
              {/each}
            </select>
          </div>
        {/each}
      {/each}
    </div>
  </div>
</div>

<style>
  .resource-board {
    min-height: calc(100vh - 200px);
  }
</style>