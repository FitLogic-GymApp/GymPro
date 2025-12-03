import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/common_widgets.dart';
import '../providers/workouts_provider.dart';
import '../models/workout_models.dart';

class WorkoutsScreen extends StatefulWidget {
  const WorkoutsScreen({super.key});

  @override
  State<WorkoutsScreen> createState() => _WorkoutsScreenState();
}

class _WorkoutsScreenState extends State<WorkoutsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<WorkoutsProvider>();
      provider.fetchFixedWorkouts();
      provider.fetchMyRoutines();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Workouts'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.primary,
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.textSecondary,
          tabs: const [
            Tab(text: 'Programs'),
            Tab(text: 'My Routines'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _FixedWorkoutsTab(),
          _MyRoutinesTab(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateRoutineDialog(context),
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  void _showCreateRoutineDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Create Routine'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Routine name',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (controller.text.trim().isNotEmpty) {
                await context
                    .read<WorkoutsProvider>()
                    .createRoutine(controller.text.trim());
                if (ctx.mounted) Navigator.pop(ctx);
                _tabController.animateTo(1);
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }
}

class _FixedWorkoutsTab extends StatelessWidget {
  const _FixedWorkoutsTab();

  @override
  Widget build(BuildContext context) {
    return Consumer<WorkoutsProvider>(
      builder: (context, provider, child) {
        if (provider.isLoading && provider.fixedWorkouts.isEmpty) {
          return const LoadingWidget();
        }

        if (provider.fixedWorkouts.isEmpty) {
          return const EmptyStateWidget(
            icon: Icons.fitness_center,
            title: 'No programs available',
          );
        }

        return RefreshIndicator(
          onRefresh: () => provider.fetchFixedWorkouts(),
          color: AppColors.primary,
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.fixedWorkouts.length,
            itemBuilder: (context, index) {
              return _WorkoutCard(workout: provider.fixedWorkouts[index]);
            },
          ),
        );
      },
    );
  }
}

class _WorkoutCard extends StatelessWidget {
  final FixedWorkout workout;

  const _WorkoutCard({required this.workout});

  @override
  Widget build(BuildContext context) {
    return GradientCard(
      onTap: () => _showWorkoutDetail(context),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              gradient: AppColors.primaryGradient,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.fitness_center,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  workout.title,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(
                      Icons.timer_outlined,
                      size: 14,
                      color: AppColors.textSecondary,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${workout.durationMin} min',
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Icon(
            Icons.chevron_right,
            color: AppColors.textHint,
          ),
        ],
      ),
    );
  }

  void _showWorkoutDetail(BuildContext context) {
    final provider = context.read<WorkoutsProvider>();
    provider.fetchFixedWorkoutDetail(workout.fixedId);

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return DraggableScrollableSheet(
          initialChildSize: 0.7,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          expand: false,
          builder: (context, scrollController) {
            return Consumer<WorkoutsProvider>(
              builder: (context, provider, child) {
                final detail = provider.selectedFixedWorkout;
                if (provider.isLoading || detail == null) {
                  return const LoadingWidget();
                }

                return SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Center(
                        child: Container(
                          width: 40,
                          height: 4,
                          decoration: BoxDecoration(
                            color: AppColors.textHint,
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        detail.title,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.timer_outlined,
                              size: 16, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            '${detail.durationMin} minutes',
                            style: const TextStyle(
                                color: AppColors.textSecondary),
                          ),
                          const SizedBox(width: 16),
                          const Icon(Icons.fitness_center,
                              size: 16, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            '${detail.exercises?.length ?? 0} exercises',
                            style: const TextStyle(
                                color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        'Exercises',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ...?detail.exercises?.map((e) => _ExerciseListItem(
                            exerciseId: e.exerciseId,
                            name: e.exerciseName,
                            muscleGroup: e.muscleGroup ?? '',
                            sets: e.sets,
                            reps: e.reps,
                            rest: e.restSec,
                          )),
                    ],
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}

class _MyRoutinesTab extends StatelessWidget {
  const _MyRoutinesTab();

  @override
  Widget build(BuildContext context) {
    return Consumer<WorkoutsProvider>(
      builder: (context, provider, child) {
        if (provider.isLoading && provider.myRoutines.isEmpty) {
          return const LoadingWidget();
        }

        if (provider.myRoutines.isEmpty) {
          return const EmptyStateWidget(
            icon: Icons.folder_open,
            title: 'No routines yet',
            subtitle: 'Tap + to create your first routine',
          );
        }

        return RefreshIndicator(
          onRefresh: () => provider.fetchMyRoutines(),
          color: AppColors.primary,
          child: ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.myRoutines.length,
            itemBuilder: (context, index) {
              return _RoutineCard(routine: provider.myRoutines[index]);
            },
          ),
        );
      },
    );
  }
}

class _RoutineCard extends StatelessWidget {
  final CustomRoutine routine;

  const _RoutineCard({required this.routine});

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: Key('routine_${routine.routineId}'),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: AppColors.error,
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Icon(Icons.delete, color: Colors.white),
      ),
      confirmDismiss: (direction) async {
        return await showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: AppColors.surface,
            title: const Text('Delete Routine'),
            content: Text('Delete "${routine.title}"?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(ctx, true),
                style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.error),
                child: const Text('Delete'),
              ),
            ],
          ),
        );
      },
      onDismissed: (direction) {
        context.read<WorkoutsProvider>().deleteRoutine(routine.routineId);
      },
      child: GradientCard(
        onTap: () => _showRoutineDetail(context),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.secondary.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.folder,
                color: AppColors.secondary,
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                routine.title,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: AppColors.textHint,
            ),
          ],
        ),
      ),
    );
  }

  void _showRoutineDetail(BuildContext context) {
    final provider = context.read<WorkoutsProvider>();
    provider.fetchRoutineDetail(routine.routineId);

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => RoutineDetailScreen(routineId: routine.routineId),
      ),
    );
  }
}

class RoutineDetailScreen extends StatefulWidget {
  final int routineId;

  const RoutineDetailScreen({super.key, required this.routineId});

  @override
  State<RoutineDetailScreen> createState() => _RoutineDetailScreenState();
}

class _RoutineDetailScreenState extends State<RoutineDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<WorkoutsProvider>().fetchRoutineDetail(widget.routineId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Routine'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddExerciseSheet(context),
          ),
        ],
      ),
      body: Consumer<WorkoutsProvider>(
        builder: (context, provider, child) {
          final routine = provider.selectedRoutine;
          if (provider.isLoading || routine == null) {
            return const LoadingWidget();
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  routine.title,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${routine.exercises?.length ?? 0} exercises',
                  style: const TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 24),
                if (routine.exercises?.isEmpty ?? true)
                  const EmptyStateWidget(
                    icon: Icons.fitness_center,
                    title: 'No exercises yet',
                    subtitle: 'Tap + to add exercises',
                  )
                else
                  ...routine.exercises!.map((e) => _ExerciseListItem(
                        routineId: widget.routineId,
                        exerciseId: e.exerciseId,
                        name: e.exerciseName,
                        muscleGroup: e.muscleGroup ?? '',
                        sets: e.sets,
                        reps: e.reps,
                        rest: e.restSec,
                        onDelete: () async {
                          final confirmed = await showDialog<bool>(
                            context: context,
                            builder: (ctx) => AlertDialog(
                              backgroundColor: AppColors.surface,
                              title: const Text('Remove Exercise', style: TextStyle(color: AppColors.textPrimary)),
                              content: Text('Remove "${e.exerciseName}" from this routine?', style: const TextStyle(color: AppColors.textSecondary)),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(ctx, false),
                                  child: const Text('Cancel'),
                                ),
                                TextButton(
                                  onPressed: () => Navigator.pop(ctx, true),
                                  child: const Text('Remove', style: TextStyle(color: AppColors.error)),
                                ),
                              ],
                            ),
                          );
                          if (confirmed == true && context.mounted) {
                            await context.read<WorkoutsProvider>().removeExerciseFromRoutine(widget.routineId, e.exerciseId);
                          }
                        },
                      )),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showAddExerciseSheet(BuildContext context) {
    final provider = context.read<WorkoutsProvider>();
    provider.fetchMuscleGroups();
    provider.fetchExercises();

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return DraggableScrollableSheet(
          initialChildSize: 0.7,
          minChildSize: 0.5,
          maxChildSize: 0.95,
          expand: false,
          builder: (context, scrollController) {
            return _AddExerciseSheet(
              routineId: widget.routineId,
              scrollController: scrollController,
            );
          },
        );
      },
    );
  }
}

class _AddExerciseSheet extends StatefulWidget {
  final int routineId;
  final ScrollController scrollController;

  const _AddExerciseSheet({
    required this.routineId,
    required this.scrollController,
  });

  @override
  State<_AddExerciseSheet> createState() => _AddExerciseSheetState();
}

class _AddExerciseSheetState extends State<_AddExerciseSheet> {
  String? _selectedMuscleGroup;
  int _sets = 3;
  int _reps = 12;
  int _restSec = 60;

  void _showExerciseConfigDialog(BuildContext context, Exercise exercise) {
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: AppColors.surface,
          title: Text(
            exercise.name,
            style: const TextStyle(color: AppColors.textPrimary),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                exercise.muscleGroup,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        const Text('Sets', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                        const SizedBox(height: 4),
                        Container(
                          decoration: BoxDecoration(
                            color: AppColors.surfaceLight,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              SizedBox(
                                width: 32,
                                height: 32,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.remove, size: 16),
                                  onPressed: () => setDialogState(() => _sets = (_sets > 1) ? _sets - 1 : 1),
                                  color: AppColors.textSecondary,
                                ),
                              ),
                              Text('$_sets', style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
                              SizedBox(
                                width: 32,
                                height: 32,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.add, size: 16),
                                  onPressed: () => setDialogState(() => _sets++),
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      children: [
                        const Text('Reps', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                        const SizedBox(height: 4),
                        Container(
                          decoration: BoxDecoration(
                            color: AppColors.surfaceLight,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              SizedBox(
                                width: 32,
                                height: 32,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.remove, size: 16),
                                  onPressed: () => setDialogState(() => _reps = (_reps > 1) ? _reps - 1 : 1),
                                  color: AppColors.textSecondary,
                                ),
                              ),
                              Text('$_reps', style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
                              SizedBox(
                                width: 32,
                                height: 32,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.add, size: 16),
                                  onPressed: () => setDialogState(() => _reps++),
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      children: [
                        const Text('Rest (s)', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                        const SizedBox(height: 4),
                        Container(
                          decoration: BoxDecoration(
                            color: AppColors.surfaceLight,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              SizedBox(
                                width: 32,
                                height: 32,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.remove, size: 16),
                                  onPressed: () => setDialogState(() => _restSec = (_restSec > 0) ? _restSec - 15 : 0),
                                  color: AppColors.textSecondary,
                                ),
                              ),
                              Text('$_restSec', style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 12)),
                              SizedBox(
                                width: 32,
                                height: 32,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  icon: const Icon(Icons.add, size: 16),
                                  onPressed: () => setDialogState(() => _restSec += 15),
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final provider = context.read<WorkoutsProvider>();
                await provider.addExerciseToRoutine(
                  routineId: widget.routineId,
                  exerciseId: exercise.exerciseId,
                  sets: _sets,
                  reps: _reps,
                  restSec: _restSec,
                );
                if (ctx.mounted) Navigator.pop(ctx);
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<WorkoutsProvider>(
      builder: (context, provider, child) {
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.textHint,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'Add Exercise',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                height: 40,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    _FilterChip(
                      label: 'All',
                      isSelected: _selectedMuscleGroup == null,
                      onTap: () {
                        setState(() => _selectedMuscleGroup = null);
                        provider.fetchExercises();
                      },
                    ),
                    ...provider.muscleGroups.map((g) => _FilterChip(
                          label: g,
                          isSelected: _selectedMuscleGroup == g,
                          onTap: () {
                            setState(() => _selectedMuscleGroup = g);
                            provider.fetchExercises(muscleGroup: g);
                          },
                        )),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: ListView.builder(
                  controller: widget.scrollController,
                  itemCount: provider.exercises.length,
                  itemBuilder: (context, index) {
                    final exercise = provider.exercises[index];
                    return ListTile(
                      title: Text(
                        exercise.name,
                        style: const TextStyle(color: AppColors.textPrimary),
                      ),
                      subtitle: Text(
                        exercise.muscleGroup,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.add_circle,
                            color: AppColors.primary),
                        onPressed: () => _showExerciseConfigDialog(context, exercise),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : AppColors.textSecondary,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

class _ExerciseListItem extends StatelessWidget {
  final int? routineId;
  final int exerciseId;
  final String name;
  final String muscleGroup;
  final int sets;
  final int reps;
  final int rest;
  final VoidCallback? onDelete;

  const _ExerciseListItem({
    this.routineId,
    required this.exerciseId,
    required this.name,
    required this.muscleGroup,
    required this.sets,
    required this.reps,
    required this.rest,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return GradientCard(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.fitness_center,
              color: AppColors.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  muscleGroup,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Row(
            children: [
              _buildStatBadge('$sets', 'sets'),
              const SizedBox(width: 6),
              _buildStatBadge('$reps', 'reps'),
              const SizedBox(width: 6),
              _buildStatBadge('${rest}s', 'rest'),
            ],
          ),
          if (onDelete != null) ...[
            const SizedBox(width: 8),
            SizedBox(
              width: 32,
              height: 32,
              child: IconButton(
                padding: EdgeInsets.zero,
                icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.error),
                onPressed: onDelete,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatBadge(String value, String label) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 13,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textHint,
            fontSize: 10,
          ),
        ),
      ],
    );
  }
}
