@extends('master.layout')

@section('title', __('Account Maintenance'))
<link rel="stylesheet" href="{{ URL::asset('css/accountmaintenance.css') }}">

@section('content')
    <div class="sub-menu">
        <div class="sub-menu-bar">
            <a class="menu-choice" href="{{ route('home') }}">{{ __('Home') }}</a>
            <a class="menu-choice" href="{{ route('cart') }}">{{ __('Cart') }}</a>
            <a class="menu-choice" href="{{ route('profile') }}">{{ __('Profile') }}</a>
            <a class="menu-choice selected" href="{{ route('account_maintenance') }}">{{ __('Account Maintenance') }}</a>
        </div>
    </div>

    <div class="container">
        <div class="account-section">
            <h2 class="account-section-title">{{ __('Account Maintenance') }}</h2>

            @if ($accounts->isEmpty())
                <div class="account-list">
                    <img class="account-list-empty-icon" src="{{ URL::asset('images/empty_icon.png') }}" alt="">
                    <h3 class="account-list-empty">{{ __('account list empty') }}</h3>
                </div>
            @else
                <div class="account-list">
                    @foreach ($accounts as $account)
                        @if ($account->delete_flag == false)
                            <form method="post" action="/delete_user/{{ $account->id }}" class="account-form">
                                @csrf
                                <div class="account-detail">
                                    @empty($account->middle_name)
                                        <h3 class="account-name">{{ $account->first_name . " " . $account->last_name }}</h3>
                                    @else
                                        <h3 class="account-name">{{ $account->first_name . " " . $account->middle_name . " " . $account->last_name }}</h3>
                                    @endempty
                                    <h5 class="account-role">{{ __('Role') }}: {{ $account->role->role_desc }}</h5>
                                </div>

                                <a class="update-btn" href="/update_role/{{ $account->id }}">
                                    <img class="update-img" src="{{ URL::asset('images/update_btn.png') }}" alt="">
                                </a>

                                <button class="delete-btn" type="submit" value="Delete">
                                    {{ __('Deactivate') }}
                                </button>
                            </form>
                        @else
                            <form method="post" action="/recover_user/{{ $account->id }}" class="account-form">
                                @csrf
                                <div class="account-detail">
                                    @empty($account->middle_name)
                                        <h3 class="account-name">{{ $account->first_name . " " . $account->last_name }}</h3>
                                    @else
                                        <h3 class="account-name">{{ $account->first_name . " " . $account->middle_name . " " . $account->last_name }}</h3>
                                    @endempty
                                    <h5 class="account-role">{{ __('Role') }}: {{ $account->role->role_desc }}</h5>
                                </div>

                                <a class="update-btn" href="/update_role/{{ $account->id }}">
                                    <img class="update-img" src="{{ URL::asset('images/update_btn.png') }}" alt="">
                                </a>

                                <button class="reactivate-btn" type="submit" value="Delete">
                                    {{ __('Reactivate') }}
                                </button>
                            </form>
                        @endif
                    @endforeach
                </div>
            @endif

            @if ($accounts->lastPage() > 1)
                <div class="pagination">
                    @if ($accounts->currentPage() > 1)
                        <a class="pagination-btn" href="{{ $accounts->url($accounts->currentPage() - 1) }}">{{ __('Previous') }}</a>
                    @endif

                    <p class="pagination-page">{{ $accounts->firstItem() }} - {{ $accounts->lastItem() }} {{ __('of') }} {{ $accounts->total() }}</p>

                    @if ($accounts->currentPage() != $accounts->lastPage())
                        <a class="pagination-btn" href="{{ $accounts->url($accounts->currentPage() + 1) }}">{{ __('Next') }}</a>
                    @endif
                </div>
            @endif
        </div>
    </div>

@endsection
