import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/turnstile_provider.dart';

class QRExitScreen extends StatefulWidget {
  const QRExitScreen({super.key});

  @override
  State<QRExitScreen> createState() => _QRExitScreenState();
}

class _QRExitScreenState extends State<QRExitScreen> 
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _pulseAnimation;
  bool _isProcessing = false;
  bool _isSuccess = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.1).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );

    _pulseAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );

    // 2 saniye sonra otomatik tarama başlat
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) _startCheckOut();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _startCheckOut() async {
    if (_isProcessing) return;
    
    setState(() => _isProcessing = true);
    
    final turnstileProvider = context.read<TurnstileProvider>();
    final success = await turnstileProvider.checkOut();
    
    if (mounted) {
      setState(() => _isSuccess = success);
      
      // 3 saniye sonra salon seçimine git
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          // Gym seçimini temizle
          final authProvider = context.read<AuthProvider>();
          authProvider.clearSelectedGym();
          context.go('/gym-selection');
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final turnstileProvider = context.watch<TurnstileProvider>();
    final gymName = authProvider.selectedGym?.name ?? 'Spor Salonu';

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => context.go('/'),
                    icon: const Icon(Icons.arrow_back, color: AppColors.textPrimary),
                  ),
                  const Spacer(),
                  Text(
                    gymName,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const Spacer(),
                  const SizedBox(width: 48),
                ],
              ),
            ),

            const Spacer(),

            // QR Code Area
            AnimatedBuilder(
              animation: _animationController,
              builder: (context, child) {
                return Transform.scale(
                  scale: _isSuccess ? 1.0 : _scaleAnimation.value,
                  child: Container(
                    width: 280,
                    height: 280,
                    decoration: BoxDecoration(
                      color: _isSuccess 
                          ? Colors.orange.withOpacity(0.2)
                          : AppColors.surface,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: _isSuccess 
                            ? Colors.orange 
                            : Colors.orange.withOpacity(_pulseAnimation.value),
                        width: 3,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.orange
                              .withOpacity(0.3 * _pulseAnimation.value),
                          blurRadius: 30,
                          spreadRadius: 5,
                        ),
                      ],
                    ),
                    child: _isSuccess
                        ? _buildSuccessContent()
                        : _buildQRContent(),
                  ),
                );
              },
            ),

            const SizedBox(height: 32),

            // Status Text
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              child: _isSuccess
                  ? Column(
                      key: const ValueKey('success'),
                      children: [
                        const Text(
                          'Çıkış Başarılı! ✓',
                          style: TextStyle(
                            color: Colors.orange,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          turnstileProvider.message ?? 'Görüşmek üzere!',
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    )
                  : Column(
                      key: const ValueKey('scanning'),
                      children: [
                        Text(
                          _isProcessing ? 'QR Kod Taranıyor...' : 'Çıkış Yapın',
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'QR kodunuzu çıkış turnikesine okutun',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
            ),

            const Spacer(),

            // Bottom Info
            Container(
              margin: const EdgeInsets.all(24),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.exit_to_app,
                      color: Colors.orange,
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Çıkış Talimatları',
                          style: TextStyle(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'QR kodunuzu çıkış turnikesine gösterin. Çıkışınız kaydedilecektir.',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 13,
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
      ),
    );
  }

  Widget _buildQRContent() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Mock QR Code Pattern
        Container(
          width: 180,
          height: 180,
          padding: const EdgeInsets.all(16),
          child: GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 8,
              mainAxisSpacing: 2,
              crossAxisSpacing: 2,
            ),
            itemCount: 64,
            itemBuilder: (context, index) {
              // Pseudo-random pattern for QR look
              final isBlack = (index % 3 == 0 || index % 7 == 0 || 
                              index < 8 || index > 55 ||
                              index % 8 == 0 || index % 8 == 7);
              return Container(
                decoration: BoxDecoration(
                  color: isBlack ? AppColors.textPrimary : Colors.transparent,
                  borderRadius: BorderRadius.circular(1),
                ),
              );
            },
          ),
        ),
        if (_isProcessing)
          const SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Colors.orange,
            ),
          ),
      ],
    );
  }

  Widget _buildSuccessContent() {
    return const Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.check_circle,
          color: Colors.orange,
          size: 120,
        ),
        SizedBox(height: 16),
        Text(
          'ÇIKIŞ',
          style: TextStyle(
            color: Colors.orange,
            fontSize: 24,
            fontWeight: FontWeight.bold,
            letterSpacing: 4,
          ),
        ),
      ],
    );
  }
}
