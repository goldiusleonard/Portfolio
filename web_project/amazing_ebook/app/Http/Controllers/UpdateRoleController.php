<?php

namespace App\Http\Controllers;

use App\Models\Role;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class UpdateRoleController extends Controller
{
    public function view($user_id) {
        $user = Auth::user();
        $roles = Role::all();
        $targetUser = User::where('id', $user_id)->first();

        if ($targetUser == null) {
            return redirect()->back();
        }

        return view('updaterole', compact('user', 'roles', 'targetUser'));
    }

    public function update_role_process(Request $request, $user_id) {
        $user = Auth::user();
        $targetUser = User::where('id', $user_id)->first();

        $targetUser->role_id = $request->role;
        $targetUser->save();

        return redirect()->route('account_maintenance');
    }
}
