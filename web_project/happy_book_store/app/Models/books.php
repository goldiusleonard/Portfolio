<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class books extends Model
{
    use HasFactory;
    public function categories() {
        return $this->belongsTo(categories::class);
    }

    public function details() {
        return $this->hasOne(details::class);
    }
}
