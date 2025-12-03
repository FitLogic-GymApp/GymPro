import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/services/auth_service.dart';

class GymSelectionScreen extends StatefulWidget {
  const GymSelectionScreen({super.key});

  @override
  State<GymSelectionScreen> createState() => _GymSelectionScreenState();
}

class _GymSelectionScreenState extends State<GymSelectionScreen> {
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadGyms();
  }

  Future<void> _loadGyms() async {
    final authProvider = context.read<AuthProvider>();
    await authProvider.fetchMyGyms();
    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _selectGym(Gym gym) async {
    final authProvider = context.read<AuthProvider>();
    await authProvider.selectGym(gym);
    if (mounted) {
      // QR giriş ekranına yönlendir
      context.go('/qr-entry');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Theme.of(context).colorScheme.primary,
              Theme.of(context).colorScheme.primary.withAlpha(200),
              Theme.of(context).scaffoldBackgroundColor,
            ],
            stops: const [0.0, 0.2, 0.4],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // Header
              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Icon(
                      Icons.fitness_center,
                      size: 48,
                      color: Colors.white,
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Salon Seçin',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Consumer<AuthProvider>(
                      builder: (context, auth, _) {
                        return Text(
                          'Hoş geldin, ${auth.user?.name ?? 'Kullanıcı'}!',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.white.withAlpha(200),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),

              // Gym List
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Theme.of(context).scaffoldBackgroundColor,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(32),
                      topRight: Radius.circular(32),
                    ),
                  ),
                  child: _isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : Consumer<AuthProvider>(
                          builder: (context, auth, _) {
                            final gyms = auth.gyms;

                            if (gyms.isEmpty) {
                              return _buildEmptyState();
                            }

                            return RefreshIndicator(
                              onRefresh: _loadGyms,
                              child: ListView.builder(
                                padding: const EdgeInsets.all(24),
                                itemCount: gyms.length,
                                itemBuilder: (context, index) {
                                  return _buildGymCard(gyms[index]);
                                },
                              ),
                            );
                          },
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final authProvider = context.read<AuthProvider>();
          await authProvider.logout();
          if (mounted) {
            context.go('/login');
          }
        },
        icon: const Icon(Icons.logout),
        label: const Text('Çıkış'),
        backgroundColor: Colors.red,
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.store_mall_directory_outlined,
              size: 80,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 24),
            const Text(
              'Henüz bir salona kayıtlı değilsiniz',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              'Bir spor salonu yöneticisinden sizi üye olarak eklemesini isteyin.',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            OutlinedButton.icon(
              onPressed: _loadGyms,
              icon: const Icon(Icons.refresh),
              label: const Text('Yenile'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGymCard(Gym gym) {
    final isActive = gym.isActive;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: isActive ? () => _selectGym(gym) : null,
        borderRadius: BorderRadius.circular(16),
        child: Opacity(
          opacity: isActive ? 1.0 : 0.5,
          child: Container(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                // Gym Icon
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primary.withAlpha(30),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    Icons.fitness_center,
                    size: 32,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 16),

                // Gym Info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        gym.name,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(
                            Icons.location_on_outlined,
                            size: 16,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              gym.location,
                              style: TextStyle(
                                color: Colors.grey[600],
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          _buildBadge(
                            gym.membershipType,
                            Colors.blue,
                          ),
                          const SizedBox(width: 8),
                          _buildBadge(
                            isActive ? 'Aktif' : 'Pasif',
                            isActive ? Colors.green : Colors.red,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // Arrow
                if (isActive)
                  Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.grey[400],
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(30),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
