<?php

use App\Http\Controllers\AccountMaintenanceController;
use App\Http\Controllers\CartController;
use App\Http\Controllers\EbookDetailController;
use App\Http\Controllers\HomeController;
use App\Http\Controllers\LogInController;
use App\Http\Controllers\LogOutController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\SignUpController;
use App\Http\Controllers\UpdateRoleController;
use Illuminate\Support\Facades\Route;

Route::get('/', [HomeController::class, 'view'])->name('home');

Route::get('/lang/{lang}', ['as' => 'lang.switch', 'uses' => 'App\Http\Controllers\LanguageController@switchLang']);

Route::middleware('guest')->group(function () {
    Route::get('/signup', [SignUpController::class, 'view'])->name('signup');
    Route::post('/signup', [SignUpController::class, 'signup_process'])->name('signup_process');

    Route::get('/login', [LogInController::class, 'view'])->name('login');
    Route::post('/login', [LogInController::class, 'login_process'])->name('login_process');
});

Route::middleware('auth')->group(function () {
    Route::get('/logout', [LogOutController::class, 'logout_process'])->name('logout_process');

    Route::get('/cart', [CartController::class, 'view'])->name('cart');
    Route::post('/cart', [CartController::class, 'checkout_process'])->name('checkout_process');

    Route::post('/delete_order/{order_id}', [CartController::class, 'delete_order_process'])->name('delete_order_process');

    Route::get('/profile', [ProfileController::class, 'view'])->name('profile');
    Route::post('/profile', [ProfileController::class, 'update_profile'])->name('update_profile');

    Route::get('/ebook_detail/{ebook_id}', [EbookDetailController::class, 'view'])->name('ebook_detail');

    Route::post('/ebook_detail/{ebook_id}', [EbookDetailController::class, 'rent_process'])->name('rent_process');

});

Route::middleware('admin')->group(function () {
    Route::get('/account_maintenance', [AccountMaintenanceController::class, 'view'])->name('account_maintenance');

    Route::get('/update_role/{user_id}', [UpdateRoleController::class, 'view'])->name('update_role');
    Route::post('/update_role/{user_id}', [UpdateRoleController::class, 'update_role_process'])->name('update_role_process');

    Route::post('/delete_user/{user_id}', [AccountMaintenanceController::class, 'delete_user_process'])->name('delete_user_process');

    Route::post('/recover_user/{user_id}', [AccountMaintenanceController::class, 'recover_user_process'])->name('recover_user_process');
});

Route::middleware('user')->group(function () {

});
