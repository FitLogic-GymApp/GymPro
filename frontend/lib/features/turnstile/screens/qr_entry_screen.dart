import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/providers/auth_provider.dart';
import '../../../core/providers/turnstile_provider.dart';

class QREntryScreen extends StatefulWidget {
  const QREntryScreen({super.key});

  @override
  State<QREntryScreen> createState() => _QREntryScreenState();
}

class _QREntryScreenState extends State<QREntryScreen> 
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
      if (mounted) _startCheckIn();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _startCheckIn() async {
    if (_isProcessing) return;
    
    setState(() => _isProcessing = true);
    
    final turnstileProvider = context.read<TurnstileProvider>();
    final success = await turnstileProvider.checkIn();
    
    if (mounted) {
      setState(() => _isSuccess = success);
      
      // 3 saniye sonra ana sayfaya git
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          context.go('/');
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
                    onPressed: () => context.go('/gym-selection'),
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
                          ? AppColors.success.withOpacity(0.2)
                          : AppColors.surface,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: _isSuccess 
                            ? AppColors.success 
                            : AppColors.primary.withOpacity(_pulseAnimation.value),
                        width: 3,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: (_isSuccess ? AppColors.success : AppColors.primary)
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
                          'Giriş Başarılı! ✓',
                          style: TextStyle(
                            color: AppColors.success,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          turnstileProvider.message ?? 'Hoş geldiniz!',
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
                          _isProcessing ? 'QR Kod Taranıyor...' : 'Turnikeden Geçin',
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'QR kodunuzu turnike okuyucusuna okutun',
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
                      color: AppColors.primary.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.info_outline,
                      color: AppColors.primary,
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Giriş Talimatları',
                          style: TextStyle(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'QR kodunuzu turnikedeki okuyucuya gösterin ve yeşil ışık yanınca geçin.',
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
              color: AppColors.primary,
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
          color: AppColors.success,
          size: 120,
        ),
        SizedBox(height: 16),
        Text(
          'GİRİŞ',
          style: TextStyle(
            color: AppColors.success,
            fontSize: 24,
            fontWeight: FontWeight.bold,
            letterSpacing: 4,
          ),
        ),
      ],
    );
  }
}
