import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'core/constants/app_colors.dart';
import 'core/theme/app_theme.dart';
import 'core/providers/auth_provider.dart';
import 'core/providers/turnstile_provider.dart';
import 'features/home/providers/home_provider.dart';
import 'features/trainers/providers/trainers_provider.dart';
import 'features/workouts/providers/workouts_provider.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/auth/screens/register_screen.dart';
import 'features/auth/screens/gym_selection_screen.dart';
import 'features/turnstile/screens/qr_entry_screen.dart';
import 'features/turnstile/screens/qr_exit_screen.dart';
import 'shared/navigation/main_navigation_shell.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AppColors.background,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  
  runApp(const GymBroApp());
}

class GymBroApp extends StatelessWidget {
  const GymBroApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => TurnstileProvider()),
        ChangeNotifierProvider(create: (_) => HomeProvider()),
        ChangeNotifierProvider(create: (_) => TrainersProvider()),
        ChangeNotifierProvider(create: (_) => WorkoutsProvider()),
      ],
      child: const _GymBroAppWithRouter(),
    );
  }
}

class _GymBroAppWithRouter extends StatefulWidget {
  const _GymBroAppWithRouter();

  @override
  State<_GymBroAppWithRouter> createState() => _GymBroAppWithRouterState();
}

class _GymBroAppWithRouterState extends State<_GymBroAppWithRouter> {
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    
    final authProvider = context.read<AuthProvider>();
    
    _router = GoRouter(
      initialLocation: '/splash',
      refreshListenable: authProvider, // AuthProvider değişince router yenilenir
      redirect: (context, state) {
        final isLoggedIn = authProvider.isLoggedIn;
        final hasSelectedGym = authProvider.hasSelectedGym;
        final authState = authProvider.state;
        final currentPath = state.matchedLocation;
        
        // Auth sayfalarında mı?
        final isAuthRoute = currentPath == '/login' || 
                           currentPath == '/register' ||
                           currentPath == '/splash';
        final isGymSelectionRoute = currentPath == '/gym-selection';
        
        // Splash ekranındaysa bekle
        if (currentPath == '/splash') {
          if (authState == AuthState.initial || authState == AuthState.loading) {
            return null; // Splash'de kal
          }
          if (!isLoggedIn) {
            return '/login';
          }
          if (!hasSelectedGym) {
            return '/gym-selection';
          }
          return '/';
        }
        
        // Login değilse ve auth sayfasında değilse login'e yönlendir
        if (!isLoggedIn && !isAuthRoute) {
          return '/login';
        }
        
        // Login ise ama auth sayfasındaysa (login/register) devam et
        if (isLoggedIn && isAuthRoute && currentPath != '/splash') {
          return hasSelectedGym ? '/' : '/gym-selection';
        }
        
        // Login ama gym seçilmemiş ve gym seçim sayfasında değilse
        if (isLoggedIn && !hasSelectedGym && !isGymSelectionRoute && !isAuthRoute) {
          return '/gym-selection';
        }
        
        return null;
      },
      routes: [
        GoRoute(
          path: '/splash',
          builder: (context, state) => const SplashScreen(),
        ),
        GoRoute(
          path: '/login',
          builder: (context, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/register',
          builder: (context, state) => const RegisterScreen(),
        ),
        GoRoute(
          path: '/gym-selection',
          builder: (context, state) => const GymSelectionScreen(),
        ),
        GoRoute(
          path: '/qr-entry',
          builder: (context, state) => const QREntryScreen(),
        ),
        GoRoute(
          path: '/qr-exit',
          builder: (context, state) => const QRExitScreen(),
        ),
        GoRoute(
          path: '/',
          builder: (context, state) => const MainNavigationShell(),
        ),
      ],
    );
    
    // Check session on app start
    WidgetsBinding.instance.addPostFrameCallback((_) {
      authProvider.checkSession();
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'GymBro',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      routerConfig: _router,
    );
  }
}

/// Splash Screen - Oturum kontrolü yapılırken gösterilir
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

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
              Theme.of(context).colorScheme.primary.withAlpha(180),
            ],
          ),
        ),
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.fitness_center,
                size: 80,
                color: Colors.white,
              ),
              SizedBox(height: 24),
              Text(
                'GymBro',
                style: TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 2,
                ),
              ),
              SizedBox(height: 48),
              CircularProgressIndicator(
                color: Colors.white,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
