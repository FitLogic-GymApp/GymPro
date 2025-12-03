import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../shared/widgets/common_widgets.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profil'),
      ),
      body: Consumer<AuthProvider>(
        builder: (context, authProvider, _) {
          final user = authProvider.user;
          final selectedGym = authProvider.selectedGym;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _buildProfileHeader(user?.name ?? 'Kullanıcı', user?.email ?? ''),
                const SizedBox(height: 16),
                _buildCurrentGymCard(context, selectedGym?.name ?? 'Salon Seçilmedi'),
                const SizedBox(height: 24),
                _buildMenuSection(context, authProvider),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildProfileHeader(String name, String email) {
    return GradientCard(
      child: Column(
        children: [
          CircleAvatar(
            radius: 48,
            backgroundColor: AppColors.primary.withOpacity(0.2),
            child: Text(
              name.isNotEmpty ? name[0].toUpperCase() : 'K',
              style: const TextStyle(
                fontSize: 36,
                fontWeight: FontWeight.bold,
                color: AppColors.primary,
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            name,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            email,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentGymCard(BuildContext context, String gymName) {
    return GradientCard(
      onTap: () => context.go('/gym-selection'),
      gradientColors: [AppColors.primary.withOpacity(0.3), AppColors.surface],
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.fitness_center,
              color: AppColors.primary,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Aktif Salonum',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  gymName,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          const Icon(
            Icons.swap_horiz,
            color: AppColors.primary,
          ),
        ],
      ),
    );
  }

  Widget _buildMenuSection(BuildContext context, AuthProvider authProvider) {
    final menuItems = [
      _MenuItem(
        icon: Icons.swap_horiz,
        title: 'Salon Değiştir',
        subtitle: 'Başka bir salona geç',
        onTap: () => context.go('/gym-selection'),
      ),
      _MenuItem(
        icon: Icons.history,
        title: 'Giriş Geçmişi',
        subtitle: 'Salon giriş/çıkış kayıtların',
        onTap: () {},
      ),
      _MenuItem(
        icon: Icons.notifications_outlined,
        title: 'Bildirimler',
        subtitle: 'Bildirim ayarları',
        onTap: () {},
      ),
      _MenuItem(
        icon: Icons.help_outline,
        title: 'Yardım & Destek',
        subtitle: 'Sıkça sorulan sorular',
        onTap: () {},
      ),
      _MenuItem(
        icon: Icons.info_outline,
        title: 'Hakkında',
        subtitle: 'Uygulama bilgileri',
        onTap: () {},
      ),
      _MenuItem(
        icon: Icons.logout,
        title: 'Çıkış Yap',
        subtitle: 'Hesabından çık',
        iconColor: AppColors.error,
        onTap: () async {
          final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('Çıkış Yap'),
              content: const Text('Hesabından çıkış yapmak istediğine emin misin?'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('İptal'),
                ),
                TextButton(
                  onPressed: () => Navigator.pop(context, true),
                  style: TextButton.styleFrom(foregroundColor: AppColors.error),
                  child: const Text('Çıkış Yap'),
                ),
              ],
            ),
          );
          if (confirmed == true) {
            await authProvider.logout();
            if (context.mounted) {
              context.go('/login');
            }
          }
        },
      ),
    ];

    return Column(
      children: menuItems.map((item) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: GradientCard(
            onTap: item.onTap,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: (item.iconColor ?? AppColors.primary).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    item.icon,
                    color: item.iconColor ?? AppColors.primary,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.title,
                        style: TextStyle(
                          color: item.iconColor ?? AppColors.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (item.subtitle != null)
                        Text(
                          item.subtitle!,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                    ],
                  ),
                ),
                Icon(
                  Icons.chevron_right,
                  color: item.iconColor ?? AppColors.textHint,
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _MenuItem {
  final IconData icon;
  final String title;
  final String? subtitle;
  final Color? iconColor;
  final VoidCallback onTap;

  _MenuItem({
    required this.icon,
    required this.title,
    this.subtitle,
    this.iconColor,
    required this.onTap,
  });
}
